# SSL证书配置说明

此目录用于存放HTTPS所需的SSL证书文件。

## 需要的文件

1. **cert.pem** - SSL证书文件
2. **key.pem** - SSL私钥文件

## 获取SSL证书的方式

### 方式1: 使用Let's Encrypt (推荐 - 免费)

使用certbot获取免费SSL证书：

```bash
# 安装certbot
sudo apt-get update
sudo apt-get install certbot

# 获取证书 (替换your-domain.com为你的域名)
sudo certbot certonly --standalone -d your-domain.com

# 证书文件位置
# fullchain.pem -> /etc/letsencrypt/live/your-domain.com/fullchain.pem
# privkey.pem -> /etc/letsencrypt/live/your-domain.com/privkey.pem

# 复制到本目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./key.pem
```

### 方式2: 自签名证书 (仅用于开发/测试)

```bash
# 生成自签名证书 (有效期365天)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

**注意**: 自签名证书会在浏览器中显示安全警告，仅适用于开发环境。

### 方式3: 购买商业SSL证书

从SSL证书提供商(如阿里云、腾讯云等)购买证书后：
1. 下载nginx格式的证书文件
2. 将证书文件重命名为 `cert.pem`
3. 将私钥文件重命名为 `key.pem`
4. 放置在此目录下

## 文件权限

确保证书文件有正确的权限：

```bash
chmod 644 cert.pem
chmod 600 key.pem
```

## 证书更新

Let's Encrypt证书有效期为90天，需要定期更新：

```bash
# 更新证书
sudo certbot renew

# 更新后重新复制到此目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./key.pem

# 重启nginx容器
docker compose -f docker/docker-compose.components.yml restart frontend
```
