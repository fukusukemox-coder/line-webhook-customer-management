#!/usr/bin/env python3.11
"""
Zoom背景動画自動生成システム
Googleフォーム回答 + LINE動画素材 → Zoom背景動画
"""

import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime
import pandas as pd
import re

# 設定
WORK_DIR = "/home/ubuntu/zoom_automation"
FORM_DATA_PATH = os.path.join(WORK_DIR, "form_responses.xlsx")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(WORK_DIR, "output")
PENDING_DIR = os.path.join(WORK_DIR, "pending")

# ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)


class ZoomBackgroundGenerator:
    """Zoom背景動画生成クラス"""
    
    def __init__(self):
        self.form_data = None
        self.load_form_data()
    
    def load_form_data(self):
        """Googleスプレッドシートからフォームデータを読み込み"""
        try:
            # Google Driveから最新データを取得
            subprocess.run([
                "rclone", "cat",
                "manus_google_drive:Zoom背景制作フォーム（回答）.xlsx",
                "--config", "/home/ubuntu/.gdrive-rclone.ini"
            ], stdout=open(FORM_DATA_PATH, 'wb'), check=True)
            
            self.form_data = pd.read_excel(FORM_DATA_PATH)
            print(f"✓ フォームデータ読み込み完了: {len(self.form_data)}件")
        except Exception as e:
            print(f"✗ フォームデータ読み込みエラー: {e}")
            self.form_data = pd.DataFrame()
    
    def find_customer_by_name(self, name):
        """名前で顧客情報を検索"""
        if self.form_data is None or len(self.form_data) == 0:
            return None
        
        # スペースを除去して検索（全角・半角両対応）
        search_name = name.replace(' ', '').replace('　', '')
        
        # 名前でマッチング（スペースを無視して部分一致）
        matches = self.form_data[
            self.form_data['お名前（必須） '].str.replace(' ', '').str.replace('　', '').str.contains(search_name, na=False)
        ]
        
        if len(matches) == 0:
            return None
        
        # 最新の回答を返す
        return matches.iloc[-1].to_dict()
    
    def generate_video(self, customer_data, video_files):
        """
        Zoom背景動画を生成
        
        Args:
            customer_data: 顧客情報（フォームデータ）
            video_files: 動画ファイルのパスリスト [cut1_video, cut2_video]
        
        Returns:
            生成された動画のパス
        """
        customer_name = customer_data.get('お名前（必須） ', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_name = f"zoom_bg_{customer_name.replace(' ', '_')}_{timestamp}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        print(f"\n=== 動画生成開始: {customer_name} ===")
        
        try:
            # 1. テンプレート画像を生成
            print("1. テンプレート画像生成中...")
            cut1_template = self._generate_cut1_template(customer_data)
            cut2_template = self._generate_cut2_template(customer_data)
            cut3_template = self._generate_cut3_template(customer_data)
            
            # 2. 各カットの動画を生成
            print("2. カット動画生成中...")
            cut1_video = self._generate_cut1_video(cut1_template, video_files[0] if len(video_files) > 0 else None)
            cut2_video = self._generate_cut2_video(cut2_template, video_files[1] if len(video_files) > 1 else None)
            cut3_video = self._generate_cut3_video(cut3_template)
            
            # 3. 動画を結合
            print("3. 動画結合中...")
            self._concat_videos([cut1_video, cut2_video, cut3_video], output_path)
            
            print(f"✓ 動画生成完了: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"✗ 動画生成エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_cut1_template(self, customer_data):
        """カット1のテンプレート画像を生成（自己紹介）"""
        # 既存のtemplate_cut1_fixed.pngをベースに使用
        base_template = os.path.join(TEMPLATE_DIR, "template_cut1_fixed.png")
        return base_template
    
    def _generate_cut2_template(self, customer_data):
        """カット2のテンプレート画像を生成（サービス紹介）"""
        # 既存のtemplate_cut2_based_on_cut1.pngをベースに使用
        base_template = os.path.join(TEMPLATE_DIR, "template_cut2_based_on_cut1.png")
        return base_template
    
    def _generate_cut3_template(self, customer_data):
        """カット3のテンプレート画像を生成（お問い合わせ）"""
        # 既存のtemplate_cut3_based_on_cut1.pngをベースに使用
        base_template = os.path.join(TEMPLATE_DIR, "template_cut3_based_on_cut1.png")
        return base_template
    
    def _generate_cut1_video(self, template_path, video_file):
        """カット1の動画を生成"""
        output = os.path.join(WORK_DIR, "temp_cut1.mp4")
        
        if video_file and os.path.exists(video_file):
            # 動画ありの場合
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", "5", "-i", template_path,
                "-t", "5", "-i", video_file,
                "-filter_complex",
                "[0:v]scale=1920:1080[bg];[1:v]scale=450:800,setsar=1[vid];[bg][vid]overlay=1435:140[v]",
                "-map", "[v]",
                "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", "5",
                output
            ]
        else:
            # 動画なしの場合（静止画のみ）
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", "5", "-i", template_path,
                "-vf", "scale=1920:1080",
                "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", "5",
                output
            ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output
    
    def _generate_cut2_video(self, template_path, video_file):
        """カット2の動画を生成"""
        output = os.path.join(WORK_DIR, "temp_cut2.mp4")
        
        if video_file and os.path.exists(video_file):
            # 動画ありの場合（16:9を9:16にクロップ）
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", "5", "-i", template_path,
                "-t", "5", "-i", video_file,
                "-filter_complex",
                "[0:v]scale=1920:1080[bg];[1:v]crop=607:1080,scale=450:800,setsar=1[vid];[bg][vid]overlay=1435:140[v]",
                "-map", "[v]",
                "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", "5",
                output
            ]
        else:
            # 動画なしの場合
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", "5", "-i", template_path,
                "-vf", "scale=1920:1080",
                "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-t", "5",
                output
            ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output
    
    def _generate_cut3_video(self, template_path):
        """カット3の動画を生成（お問い合わせ）"""
        output = os.path.join(WORK_DIR, "temp_cut3.mp4")
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", "5", "-i", template_path,
            "-vf", "scale=1920:1080",
            "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-t", "5",
            output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output
    
    def _concat_videos(self, video_files, output_path):
        """複数の動画を結合"""
        concat_list = os.path.join(WORK_DIR, "concat_list.txt")
        
        with open(concat_list, 'w') as f:
            for video in video_files:
                f.write(f"file '{video}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)


def main():
    """メイン処理"""
    print("=== Zoom背景動画自動生成システム ===")
    
    # テスト用: コマンドライン引数から名前と動画ファイルを受け取る
    if len(sys.argv) < 2:
        print("使用方法: python zoom_bg_automation.py <顧客名> [動画1] [動画2]")
        print("例: python zoom_bg_automation.py '福山修平' video1.mp4 video2.mp4")
        sys.exit(1)
    
    customer_name = sys.argv[1]
    video_files = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # 生成処理
    generator = ZoomBackgroundGenerator()
    
    # 顧客情報を検索
    customer_data = generator.find_customer_by_name(customer_name)
    if customer_data is None:
        print(f"✗ 顧客情報が見つかりません: {customer_name}")
        sys.exit(1)
    
    print(f"✓ 顧客情報取得: {customer_data.get('お名前（必須） ')}")
    print(f"  - 表示名: {customer_data.get('表示名（店名・屋号）')}")
    print(f"  - 肩書き: {customer_data.get('肩書き（必須）')}")
    print(f"  - キャッチ: {customer_data.get('ひと言キャッチ（任意／18文字まで）')}")
    
    # 動画生成
    output_video = generator.generate_video(customer_data, video_files)
    
    if output_video:
        print(f"\n✓ 完成: {output_video}")
    else:
        print("\n✗ 動画生成に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
