#!/usr/bin/env python3
"""
GCS 存储桶清理脚本
用于清理 auditai-claims-bucket 中的文件，释放存储空间
"""

from google.cloud import storage
import sys

def clean_gcs_bucket(bucket_name="auditai-claims-bucket"):
    """清理GCS存储桶中的所有文件"""
    
    print(f"🧹 GCS存储桶清理脚本")
    print("=" * 50)
    print(f"目标存储桶: {bucket_name}")
    
    try:
        # 初始化存储客户端
        print("\n📝 连接到Google Cloud Storage...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # 检查存储桶是否存在
        if not bucket.exists():
            print(f"❌ 存储桶 '{bucket_name}' 不存在")
            return False
        
        print("✅ 成功连接到存储桶")
        
        # 列出所有文件
        print("\n📄 列出存储桶中的文件...")
        blobs = list(bucket.list_blobs())
        
        if not blobs:
            print("✅ 存储桶已经是空的，无需清理")
            return True
        
        print(f"📊 找到 {len(blobs)} 个文件:")
        total_size = 0
        
        for i, blob in enumerate(blobs, 1):
            size_mb = blob.size / 1024 / 1024 if blob.size else 0
            total_size += size_mb
            print(f"  {i}. {blob.name} ({size_mb:.2f} MB)")
        
        print(f"\n📊 总大小: {total_size:.2f} MB")
        
        # 确认删除
        print("\n⚠️ 警告：这将永久删除存储桶中的所有文件！")
        confirm = input("确认删除所有文件？(yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ 操作已取消")
            return False
        
        # 执行删除
        print(f"\n🗑️ 开始删除 {len(blobs)} 个文件...")
        
        deleted_count = 0
        for i, blob in enumerate(blobs, 1):
            try:
                blob.delete()
                deleted_count += 1
                print(f"✅ 已删除 ({i}/{len(blobs)}): {blob.name}")
            except Exception as e:
                print(f"❌ 删除失败 ({i}/{len(blobs)}): {blob.name} - {e}")
        
        print(f"\n🎉 清理完成！")
        print(f"✅ 成功删除: {deleted_count} 个文件")
        print(f"❌ 删除失败: {len(blobs) - deleted_count} 个文件")
        print(f"💾 释放空间: {total_size:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

def list_bucket_contents(bucket_name="auditai-claims-bucket"):
    """仅查看存储桶内容，不删除"""
    
    print(f"📋 查看存储桶内容")
    print("=" * 50)
    print(f"存储桶: {bucket_name}")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        if not bucket.exists():
            print(f"❌ 存储桶 '{bucket_name}' 不存在")
            return
        
        blobs = list(bucket.list_blobs())
        
        if not blobs:
            print("✅ 存储桶是空的")
            return
        
        print(f"\n📊 找到 {len(blobs)} 个文件:")
        total_size = 0
        
        for i, blob in enumerate(blobs, 1):
            size_mb = blob.size / 1024 / 1024 if blob.size else 0
            total_size += size_mb
            created = blob.time_created.strftime("%Y-%m-%d %H:%M:%S") if blob.time_created else "未知"
            print(f"  {i}. {blob.name}")
            print(f"     大小: {size_mb:.2f} MB")
            print(f"     创建时间: {created}")
            print()
        
        print(f"📊 总计: {len(blobs)} 个文件, {total_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ 查看失败: {e}")

def main():
    """主函数"""
    print("🔧 Google Cloud Storage 管理工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看存储桶内容")
        print("2. 清理存储桶（删除所有文件）")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1/2/3): ").strip()
        
        if choice == "1":
            list_bucket_contents()
        elif choice == "2":
            clean_gcs_bucket()
        elif choice == "3":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main() 