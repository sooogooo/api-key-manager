#!/bin/bash
# Docker管理脚本
# 用法: ./docker-manage.sh [命令] [参数]

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查docker和docker-compose是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker未安装${NC}"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose未安装${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo -e "${GREEN}API密钥管理系统 Docker管理脚本${NC}"
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "可用命令:"
    echo "  start        - 启动所有服务"
    echo "  stop         - 停止所有服务"
    echo "  restart      - 重启所有服务"
    echo "  rebuild      - 重新构建并启动服务"
    echo "  logs [服务]  - 查看服务日志 (可选: web|db|redis|nginx)"
    echo "  status       - 查看服务状态"
    echo "  backup       - 备份数据库"
    echo "  restore [文件] - 恢复数据库"
    echo "  shell [服务]  - 进入服务容器的shell (web|db|redis|nginx)"
    echo "  clean        - 清理未使用的Docker资源"
    echo "  update       - 更新应用（拉取最新代码并重建）"
    echo ""
    echo "示例:"
    echo "  $0 start"
    echo "  $0 logs web"
    echo "  $0 backup"
    echo "  $0 restore backup_20240120.sql"
}

# 启动服务
start_services() {
    echo -e "${GREEN}启动所有服务...${NC}"
    docker-compose up -d
    echo -e "${GREEN}服务已启动${NC}"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止所有服务...${NC}"
    docker-compose down
    echo -e "${GREEN}服务已停止${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}重启所有服务...${NC}"
    docker-compose restart
    echo -e "${GREEN}服务已重启${NC}"
}

# 重建服务
rebuild_services() {
    echo -e "${YELLOW}重新构建并启动服务...${NC}"
    docker-compose up --build -d
    echo -e "${GREEN}服务已重建并启动${NC}"
}

# 查看日志
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# 查看状态
check_status() {
    echo -e "${GREEN}服务状态:${NC}"
    docker-compose ps
    echo -e "\n${GREEN}资源使用情况:${NC}"
    docker stats --no-stream
}

# 备份数据库
backup_database() {
    local backup_dir="backups"
    local date_str=$(date +%Y%m%d_%H%M%S)
    local backup_file="${backup_dir}/db_backup_${date_str}.sql"
    
    mkdir -p "$backup_dir"
    echo -e "${GREEN}开始备份数据库...${NC}"
    docker-compose exec -T db pg_dump -U aiproxy ai_proxy > "$backup_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}数据库已备份到: ${backup_file}${NC}"
    else
        echo -e "${RED}备份失败${NC}"
        rm -f "$backup_file"
    fi
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}错误: 备份文件不存在${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}警告: 这将覆盖当前数据库内容${NC}"
    read -p "是否继续? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}开始恢复数据库...${NC}"
        cat "$backup_file" | docker-compose exec -T db psql -U aiproxy ai_proxy
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}数据库已恢复${NC}"
        else
            echo -e "${RED}恢复失败${NC}"
        fi
    fi
}

# 进入容器shell
enter_shell() {
    local service=$1
    if [ -z "$service" ]; then
        echo -e "${RED}错误: 请指定服务名称 (web|db|redis|nginx)${NC}"
        return 1
    fi
    docker-compose exec "$service" sh
}

# 清理Docker资源
clean_docker() {
    echo -e "${YELLOW}清理未使用的Docker资源...${NC}"
    docker system prune -f
    echo -e "${GREEN}清理完成${NC}"
}

# 更新应用
update_app() {
    echo -e "${GREEN}更新应用...${NC}"
    echo -e "${YELLOW}1. 拉取最新代码${NC}"
    git pull
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}拉取代码失败${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}2. 重新构建并启动服务${NC}"
    docker-compose up --build -d
    
    echo -e "${YELLOW}3. 执行数据库迁移${NC}"
    docker-compose exec web flask db upgrade
    
    echo -e "${GREEN}更新完成${NC}"
}

# 主函数
main() {
    check_docker
    
    case "$1" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        rebuild)
            rebuild_services
            ;;
        logs)
            view_logs "$2"
            ;;
        status)
            check_status
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$2"
            ;;
        shell)
            enter_shell "$2"
            ;;
        clean)
            clean_docker
            ;;
        update)
            update_app
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"