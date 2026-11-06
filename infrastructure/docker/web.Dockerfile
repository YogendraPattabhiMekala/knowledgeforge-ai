FROM node:22.22.1-alpine AS builder
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
ARG API_INTERNAL_URL=http://api:8000
ENV API_INTERNAL_URL=$API_INTERNAL_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build
FROM node:22.22.1-alpine
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000 NEXT_TELEMETRY_DISABLED=1
RUN addgroup -S forge && adduser -S forge -G forge
COPY --from=builder --chown=forge:forge /app/.next/standalone ./
COPY --from=builder --chown=forge:forge /app/.next/static ./.next/static
USER forge
EXPOSE 3000
CMD ["node","server.js"]
