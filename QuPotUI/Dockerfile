FROM node:16.15.0-alpine as stage-build
WORKDIR /data


# RUN apk add python2 make gcc g++

COPY ./package.json /data/package.json

COPY ./package-lock.json /data/package-lock.json

# node:14 不使用 package-lock.json, 使用 npm config set 的源，node:16 使用 package-lock.json 中的源

# Continuous Integration（持续集成）模式，完全忽略 package.json 文件中的 dependencies 和 devDependencies 字段之外的所有字段，并根据 package-lock.json 或 npm-shrinkwrap.json 文件的精确版本信息安装依赖项，以确保每次安装的依赖项都是相同的。
RUN npm ci
COPY . /data
RUN npm run-script build

FROM nginx:alpine

COPY --from=stage-build /data/dist /opt/ui
COPY nginx.conf /etc/nginx/conf.d/default.conf
