#!/bin/bash

# Advanced OCR 服务健康检查

echo "🔍 检查 Advanced OCR 服务状态..."
echo ""

# 检查后端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "后端服务 (http://localhost:8005)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查进程
if ps aux | grep -v grep | grep "python.*web/backend/app.py" > /dev/null; then
    echo "✅ 进程: 运行中"
    PID=$(ps aux | grep -v grep | grep "python.*web/backend/app.py" | awk '{print $2}' | head -1)
    echo "   PID: $PID"
else
    echo "❌ 进程: 未运行"
fi

# 检查端口
if lsof -i :8005 > /dev/null 2>&1; then
    echo "✅ 端口: 8005 已监听"
else
    echo "❌ 端口: 8005 未监听"
fi

# 检查 HTTP 响应
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8005/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "000" ]; then
    echo "✅ HTTP: 响应码 $HTTP_CODE"
else
    echo "❌ HTTP: 无响应"
fi

echo ""

# 检查前端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "前端服务 (http://localhost:5173)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查进程
if ps aux | grep -v grep | grep "vite" > /dev/null; then
    echo "✅ 进程: 运行中"
    PID=$(ps aux | grep -v grep | grep "vite" | awk '{print $2}' | head -1)
    echo "   PID: $PID"
else
    echo "❌ 进程: 未运行"
fi

# 检查端口
if lsof -i :5173 > /dev/null 2>&1; then
    echo "✅ 端口: 5173 已监听"
else
    echo "❌ 端口: 5173 未监听"
fi

# 检查 HTTP 响应
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ HTTP: 响应正常 ($HTTP_CODE)"
else
    echo "⚠️  HTTP: 响应码 $HTTP_CODE"
fi

echo ""

# 总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BACKEND_OK=false
FRONTEND_OK=false

if ps aux | grep -v grep | grep "python.*web/backend/app.py" > /dev/null && [ "$HTTP_CODE" != "000" ]; then
    BACKEND_OK=true
fi

if ps aux | grep -v grep | grep "vite" > /dev/null; then
    FRONTEND_OK=true
fi

if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
    echo "✅ 所有服务运行正常"
    echo ""
    echo "📊 访问地址:"
    echo "   前端: http://localhost:5173"
    echo "   后端: http://localhost:8005"
elif [ "$BACKEND_OK" = false ] && [ "$FRONTEND_OK" = false ]; then
    echo "❌ 所有服务未运行"
    echo ""
    echo "🚀 启动服务: ./start_local.sh"
elif [ "$BACKEND_OK" = false ]; then
    echo "⚠️  后端服务未运行"
    echo ""
    echo "📝 查看后端日志: tail -f logs/backend.log"
else
    echo "⚠️  前端服务未运行"
    echo ""
    echo "📝 查看前端日志: tail -f logs/frontend.log"
fi

echo ""
