import sys
from pathlib import Path

# Add backend directory to path to ensure absolute imports work
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.db_manager import db_session, DB_TYPE

def reset_database():
    print(f"[*] 正在準備重置資料庫... (當前配置類型: {DB_TYPE.upper()})")
    print("⚠️  注意：此操作將會清空所有的歷史選股推薦 (recommendations) 與週報存檔 (reports)。")
    
    # In crontab or automated run, we can bypass confirm if needed, but since this is manually run:
    try:
        confirm = input("⚠️  您確定要清空資料庫以開啟乾淨的 1 個月實戰觀測嗎？ [y/N]: ")
    except (KeyboardInterrupt, EOFError):
        print("\n[!] 輸入中斷，操作取消。")
        return
        
    if confirm.strip().lower() != 'y':
        print("[!] 操作已取消，資料庫未做任何變更。")
        return
        
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            if DB_TYPE == "mysql":
                # MySQL uses TRUNCATE to reset auto-increment primary keys
                cursor.execute("TRUNCATE TABLE recommendations;")
                cursor.execute("TRUNCATE TABLE reports;")
                print("[✓] MySQL 資料庫 recommendations 與 reports 表已成功 TRUNCATE 清空！")
            else:
                # SQLite fallback
                cursor.execute("DELETE FROM recommendations;")
                cursor.execute("DELETE FROM reports;")
                cursor.execute("VACUUM;")
                print("[✓] SQLite 資料庫已成功清空並執行收縮 (VACUUM)！")
    except Exception as e:
        print(f"[✗] 清空資料庫時發生異常: {e}")

if __name__ == "__main__":
    reset_database()
