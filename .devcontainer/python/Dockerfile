ARG PYTHON_VERSION="3.10.13"
FROM python:${PYTHON_VERSION}-slim

ARG NODE_VERSION="24.5.0"

EXPOSE 8088

ENV TZ=Asia/Tokyo

# 各種パッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    fonts-ipaexfont \
    libopencv-dev \
    sqlite3 \
    lhasa \
    wget \
    locales \
    ffmpeg \
    fonts-noto-cjk && rm -rf /var/lib/apt/lists/*

# GitHub CLIのインストール
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y gh

# Node.jsのインストール
# Node.jsのバージョンは必要に応じて変更してください
RUN curl -fsSL https://deb.nodesource.com/setup_$(echo "$NODE_VERSION" | cut -d . -f 1).x | bash - \
    && apt-get install -y nodejs

# 日本語環境の設定
ENV LANG ja_JP.UTF-8
ENV LC_ALL ja_JP.UTF-8
RUN sed -i '$d' /etc/locale.gen \
    && echo "ja_JP.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen ja_JP.UTF-8 \
    && /usr/sbin/update-locale LANG=ja_JP.UTF-8 LANGUAGE="ja_JP:ja"
RUN /bin/bash -c "source /etc/default/locale"
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

WORKDIR /app

# Pythonパッケージのインストール
COPY requirements.txt /app
RUN pip install -r requirements.txt
RUN python -m playwright install chromium
RUN python -m playwright install-deps 

# Google Gemini CLIのインストール
RUN npm install -g @google/gemini-cli
