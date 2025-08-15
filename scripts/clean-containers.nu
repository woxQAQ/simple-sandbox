#!/usr/bin/env nu

# 清理指定镜像的正在运行的 podman 容器
# Clean up running podman containers for specified images

def main [...images: string] {
    if ($images | length) == 0 {
        print "错误: 请指定至少一个镜像名称"
        print "用法: nu clean-containers.nu <image1> [image2] [image3] ..."
        print "示例: nu clean-containers.nu nginx:latest redis:alpine"
        return
    }
    
    print $"正在查找使用镜像 ($images | str join ', ') 的运行中容器..."
    
    # 获取所有正在运行的容器信息（包含镜像名）
    let all_containers = (podman ps --format "{{.ID}}\t{{.Image}}" | lines | where $it != "")
    
    if ($all_containers | length) == 0 {
        print "没有找到正在运行的容器"
        return
    }
    
    # 过滤出匹配指定镜像的容器
    let matching_containers = ($all_containers | each { |line|
        let parts = ($line | split column "\t" container_id image)
        let container_id = $parts.container_id.0
        let image = $parts.image.0
        
        # 检查容器镜像是否匹配任何指定的镜像
        let matches = ($images | any { |target_image|
            ($image | str contains $target_image) or ($image == $target_image)
        })
        
        if $matches {
            {container_id: $container_id, image: $image}
        }
    } | where $it != null)
    
    if ($matching_containers | length) == 0 {
        print $"没有找到使用镜像 ($images | str join ', ') 的运行中容器"
        return
    }
    
    print $"找到 ($matching_containers | length) 个匹配的容器:"
    for container in $matching_containers {
        print $"  - 容器 ($container.container_id): ($container.image)"
    }
    
    # 停止匹配的容器
    for container in $matching_containers {
        print $"正在停止容器: ($container.container_id) \(镜像: ($container.image)\)"
        try {
            podman stop $container.container_id
            print $"✓ 容器 ($container.container_id) 已停止"
        } catch {
            print $"✗ 停止容器 ($container.container_id) 失败"
        }
    }
    
    print "指定镜像的容器停止操作完成"
}