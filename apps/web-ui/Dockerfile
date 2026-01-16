FROM node:22-alpine

WORKDIR /app

COPY apps/web-ui/package.json apps/web-ui/package-lock.json* ./ 
RUN npm install

COPY apps/web-ui ./

EXPOSE 3100

CMD ["npm", "run", "dev"]

