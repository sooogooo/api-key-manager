#!/bin/bash
# 生成自签名SSL证书脚本
# 用法: ./generate_ssl_cert.sh [域名]

# 设置默认域名为localhost
DOMAIN=${1:-localhost}
SSL_DIR="./ssl"

# 创建SSL目录
mkdir -p $SSL_DIR

echo "正在为域名 $DOMAIN 生成自签名SSL证书..."

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout $SSL_DIR/server.key \
  -out $SSL_DIR/server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# 设置适当的权限
chmod 600 $SSL_DIR/server.key
chmod 644 $SSL_DIR/server.crt

echo "SSL证书已生成:"
echo "私钥: $SSL_DIR/server.key"
echo "证书: $SSL_DIR/server.crt"
echo ""
echo "这些文件将被Docker容器使用。如果你需要在浏览器中信任此证书，请将 $SSL_DIR/server.crt 导入到你的浏览器或操作系统的证书存储中。"