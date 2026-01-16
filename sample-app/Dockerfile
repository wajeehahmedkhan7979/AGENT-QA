FROM node:22-alpine

WORKDIR /app

COPY sample-app/package.json sample-app/package-lock.json* /app/
RUN npm install --omit=dev || npm install

COPY sample-app /app

EXPOSE 3000

CMD ["node", "server.js"]

