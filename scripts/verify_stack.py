"""No-paid-provider acceptance test against the REAL web/API/worker stack.
Creates synthetic test users and deletes its documents; no schema truncation.
Usage: python scripts/verify_stack.py http://localhost:3001
"""
import asyncio, sys, time, uuid
import httpx

async def register(client, email):
    response=await client.post('/api/auth/register',json={'name':'Acceptance Tester','organization':'Synthetic Acceptance '+uuid.uuid4().hex[:8],'email':email,'password':'SyntheticTestPassword!2026'})
    response.raise_for_status()
    client.headers['X-CSRF-Token']=response.json()['csrf']
    me=(await client.get('/api/auth/me')).json()
    return me['organizations'][0]['id']

async def main(url):
    async with httpx.AsyncClient(base_url=url,timeout=30) as owner, httpx.AsyncClient(base_url=url,timeout=30) as outsider:
        health=(await owner.get('/api/health')).json()
        assert health['generation']=='extractive', 'Refusing provider-enabled acceptance run without approval'
        assert health['retrieval']=='postgres-full-text',health
        marker=uuid.uuid4().hex[:12];email='acceptance-'+marker+'@example.test'
        org=await register(owner,'owner-'+email)
        other_org=await register(outsider,email)
        root=f'/api/organizations/{org}'
        workspace=await owner.post(root+'/workspaces',json={'name':'Acceptance Research','description':'Synthetic validation fixture'})
        workspace.raise_for_status();wid=workspace.json()['id']
        payload=b'Synthetic policy: Remote work is permitted three days per week. Contact the team lead for approval.'
        uploaded=await owner.post(root+'/documents',data={'workspace_id':wid},files={'file':('synthetic-policy.md',payload,'text/markdown')})
        uploaded.raise_for_status();did=uploaded.json()['id']
        assert uploaded.json()['status']=='queued', 'Expected asynchronous queue dispatch'
        for _ in range(60):
            detail=(await owner.get(root+'/documents/'+did)).json()
            if detail['status'] in {'ready','failed'}:break
            await asyncio.sleep(.5)
        assert detail['status']=='ready' and detail['chunks']>0,detail
        assert detail['attempts']>=1
        assert (await owner.get(root+'/documents/'+did+'/download')).content==payload
        hits=await owner.get(root+'/search',params={'q':'remote work policy'})
        hits.raise_for_status();assert hits.json()[0]['document_id']==did
        chat=await owner.post(root+'/chat',json={'question':'What is the remote work policy?'})
        chat.raise_for_status();answer=chat.json()
        assert 'Extractive mode' in answer['content'] and answer['citations'][0]['document_id']==did
        cid=answer['conversation_id']
        assert (await outsider.get(root+'/documents/'+did+'/download')).status_code==404
        assert (await outsider.get(f'/api/organizations/{other_org}/search',params={'q':'remote'})).json()==[]
        grant=await owner.post(root+'/members',json={'email':email,'role':'viewer'});grant.raise_for_status()
        assert (await outsider.get(root+'/documents')).json()[0]['id']==did
        assert (await outsider.post(root+'/chat',json={'question':'remote work'})).status_code==403
        update=await owner.patch(root+'/documents/'+did,json={'visibility':'private','workspace_id':wid});update.raise_for_status()
        assert (await outsider.get(root+'/documents')).json()==[]
        assert (await outsider.get(root+'/search',params={'q':'remote'})).json()==[]
        deleted=await owner.delete(root+'/documents/'+did);deleted.raise_for_status()
        assert (await owner.get(root+'/documents/'+did+'/download')).status_code==404
        assert (await owner.get(root+'/search',params={'q':'remote'})).json()==[]
        history=(await owner.get(root+'/conversations/'+cid)).json()
        assert history[1]['citations']==[] and 'hidden' in history[1]['content']
        (await owner.delete(root+'/conversations/'+cid)).raise_for_status()
        (await owner.delete(root+'/workspaces/'+wid)).raise_for_status()
        print('PASS: PostgreSQL → S3 upload → Celery ingestion → full-text retrieval → LangGraph extractive chat → citations → tenant/viewer/private checks → deletion')

if __name__=='__main__':asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:3001'))
