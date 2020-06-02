# FROM node:10.16.0

# COPY . /frontend
# WORKDIR /frontend
# RUN npm install
# RUN npm run build
FROM nginx:1.16.0

# COPY --from=0 /frontend/dist /frontend/dist
COPY dist /frontend/dist
COPY nginx.conf /etc/nginx/nginx.conf
