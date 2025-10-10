# Docker权限问题解决方案

## 问题描述

运行 `./deploy.sh` 时出现错误：
```
permission denied while trying to connect to the Docker daemon socket
```

这是因为当前用户没有权限访问Docker。

## 解决方案

### 方案1: 添加用户到docker组（推荐）

**快速修复：**
```bash
./fix_docker_permission.sh
```

**手动修复：**
```bash
# 1. 添加当前用户到docker组
sudo usermod -aG docker $USER

# 2. 激活权限（选择其一）
# 选项A: 重新登录系统
logout  # 或注销/重启

# 选项B: 在当前shell激活（临时）
newgrp docker

# 3. 验证权限
docker ps

# 4. 重新运行部署
./deploy.sh
```

### 方案2: 使用sudo运行（临时方案）

```bash
sudo ./deploy.sh
```

**注意：** 使用sudo会导致生成的文件属于root，可能需要后续修改权限。

### 方案3: 使用sudo运行所有Docker命令

如果不想修改用户组，可以在所有docker命令前加sudo：

```bash
cd docker
sudo docker-compose up -d --build
```

## 验证权限

运行以下命令验证Docker权限：

```bash
# 应该能看到容器列表（即使是空的）
docker ps

# 应该能看到Docker版本信息
docker version
```

## 推荐方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| 添加到docker组 | 永久生效，使用方便 | 需要重新登录 | ⭐⭐⭐⭐⭐ |
| 使用sudo | 立即可用 | 每次都要输入密码，文件权限问题 | ⭐⭐ |

## 安全说明

将用户添加到docker组等同于给予该用户root权限，因为：
- Docker容器可以挂载主机任意目录
- Docker容器可以以root身份运行

**生产环境建议：**
- 只将受信任的用户添加到docker组
- 使用专门的服务账号运行Docker服务
- 配置Docker的访问控制和审计

## 故障排除

### 问题1: 添加到组后仍无权限

```bash
# 检查当前用户所在的组
groups

# 如果没看到docker组，需要重新登录
# 或使用 newgrp docker 临时激活
```

### 问题2: sudo也无法运行

```bash
# 检查Docker服务是否运行
sudo systemctl status docker

# 如果没运行，启动Docker服务
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker
```

### 问题3: 仍然报错

```bash
# 检查Docker socket文件
ls -l /var/run/docker.sock

# 应该看到类似输出：
# srw-rw---- 1 root docker 0 xxx  /var/run/docker.sock

# 如果docker组没有rw权限，手动修复
sudo chmod 666 /var/run/docker.sock  # 临时修复
# 或
sudo systemctl restart docker  # 永久修复
```

## 完整部署流程

```bash
# 1. 修复权限
./fix_docker_permission.sh

# 2. 重新登录或激活
newgrp docker

# 3. 运行部署
./deploy.sh

# 4. 验证服务
docker ps
curl http://localhost:8005/
curl http://localhost:5173/
```

## WSL2用户注意事项

如果在WSL2中使用Docker Desktop：

1. 确保Docker Desktop已启动
2. 在Docker Desktop设置中启用WSL2集成
3. 选择要使用的WSL2发行版

## macOS用户注意事项

macOS用户通常不会遇到权限问题，因为Docker Desktop会自动处理权限。

如果遇到问题：
1. 重启Docker Desktop
2. 检查Docker Desktop设置中的权限配置
