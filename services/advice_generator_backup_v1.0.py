from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AdviceGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """
        アドバイス生成器の初期化
        
        Args:
            api_key: OpenAI API キー（オプション）
        """
        self.api_key = api_key
        self.client = None
        
        if api_key:
            try:
                # OpenAI v1.0+ 対応
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                logger.info("OpenAI クライアント初期化成功（v1.0+）")
            except ImportError:
                try:
                    # OpenAI v0.x 対応
                    import openai
                    openai.api_key = api_key
                    logger.info("OpenAI API キー設定成功（v0.x）")
                except ImportError:
                    logger.error("OpenAI ライブラリがインストールされていません")
    
    def generate_advice(self, analysis_data: Dict, use_chatgpt: bool = False) -> Dict:
        """
        解析データに基づいてアドバイスを生成
        
        Args:
            analysis_data: 動作解析データ
            use_chatgpt: ChatGPT APIを使用するかどうか
            
        Returns:
            アドバイスデータ
        """
        try:
            logger.info(f"アドバイス生成開始 - ChatGPT使用: {use_chatgpt}, APIキー: {'あり' if self.api_key else 'なし'}")
            
            # 基本アドバイスを生成
            basic_advice = self._generate_basic_advice(analysis_data)
            
            if use_chatgpt and self.api_key:
                logger.info("ChatGPT詳細アドバイス生成を開始")
                # ChatGPT APIを使用して詳細アドバイスを生成
                enhanced_advice = self._generate_enhanced_advice(analysis_data, basic_advice)
                logger.info(f"ChatGPT詳細アドバイス生成完了 - Enhanced: {enhanced_advice.get('enhanced', False)}")
                return enhanced_advice
            else:
                logger.info("基本アドバイスのみ生成")
                return basic_advice
                
        except Exception as e:
            logger.error(f"アドバイス生成エラー: {e}")
            return self._generate_fallback_advice()
    
    def _generate_basic_advice(self, analysis_data: Dict) -> Dict:
        """基本的なアドバイスを生成"""
        total_score = analysis_data.get('total_score', 0)
        phase_analysis = analysis_data.get('phase_analysis', {})
        
        # 総合評価
        if total_score >= 8:
            overall = "素晴らしいサービスフォームです！細かい調整でさらに向上できます。"
        elif total_score >= 6:
            overall = "良好なサービスフォームです。いくつかの改善点があります。"
        elif total_score >= 4:
            overall = "基本的なフォームはできています。重要なポイントを改善しましょう。"
        else:
            overall = "フォームに改善の余地があります。基礎から見直しましょう。"
        
        # 技術的ポイント
        technical_points = []
        practice_suggestions = []
        
        for phase, data in phase_analysis.items():
            score = data.get('score', 0)
            if score < 6:
                if phase == "準備フェーズ":
                    technical_points.append("スタンス幅を肩幅程度に調整し、体重を前足に乗せましょう")
                    practice_suggestions.append("壁打ちで正しいスタンスを練習する")
                elif phase == "トスフェーズ":
                    technical_points.append("トスの高さと位置を一定にしましょう")
                    practice_suggestions.append("トスのみの練習を毎日50回行う")
                elif phase == "バックスイングフェーズ":
                    technical_points.append("ラケットを大きく引いて、肩の回転を意識しましょう")
                    practice_suggestions.append("シャドースイングで正しいバックスイングを身につける")
                elif phase == "インパクトフェーズ":
                    technical_points.append("インパクト時の体重移動とラケット面を安定させましょう")
                    practice_suggestions.append("低いネットでのサービス練習")
                elif phase == "フォロースルーフェーズ":
                    technical_points.append("フォロースルーを大きく取り、体の回転を完了させましょう")
                    practice_suggestions.append("フォロースルーを意識したスローモーション練習")
        
        return {
            "overall_advice": overall,
            "technical_points": technical_points[:5],  # 最大5つ
            "practice_suggestions": practice_suggestions[:5],  # 最大5つ
            "enhanced": False
        }
    
    def _generate_enhanced_advice(self, analysis_data: Dict, basic_advice: Dict) -> Dict:
        """ChatGPT APIを使用して詳細なアドバイスを生成"""
        try:
            logger.info("ChatGPT API呼び出し開始")
            
            # 解析データを整理
            total_score = analysis_data.get('total_score', 0)
            phase_analysis = analysis_data.get('phase_analysis', {})
            
            # ChatGPTへの簡潔なプロンプトを作成
            prompt = self._create_compact_prompt(total_score, phase_analysis, basic_advice)
            
            # ChatGPT APIを呼び出し
            ai_response = self._call_chatgpt_api(prompt)
            
            if ai_response:
                logger.info("ChatGPT API呼び出し成功")
                # レスポンスを解析
                enhanced_advice = self._parse_ai_response(ai_response, basic_advice)
                enhanced_advice["enhanced"] = True
                enhanced_advice["detailed_advice"] = ai_response
                return enhanced_advice
            else:
                logger.error("ChatGPT APIからの応答が空です")
                basic_advice["enhanced"] = False
                basic_advice["error"] = "ChatGPT APIからの応答が空でした"
                return basic_advice
            
        except Exception as e:
            logger.error(f"ChatGPT API呼び出しエラー: {e}")
            # エラー時は基本アドバイスを返す
            basic_advice["enhanced"] = False
            basic_advice["error"] = f"ChatGPT接続エラー: {str(e)}"
            return basic_advice
    
    def _call_chatgpt_api(self, prompt: str) -> str:
        """ChatGPT APIを呼び出し"""
        try:
            if self.client:
                # OpenAI v1.0+ 対応
                logger.info("OpenAI v1.0+ APIを使用")
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # GPT-4oを使用
                    messages=[
                        {
                            "role": "system",
                            "content": """あなたは30年以上の経験を持つATP/WTAツアーのプロテニスコーチです。グランドスラム優勝者を指導した実績があり、スポーツ科学博士号（バイオメカニクス専門）を持っています。

テニスサービスの動作解析結果に基づいて、世界基準の詳細なアドバイスを提供してください。以下の形式で回答してください：

1. 現在のフォームと理想フォームの具体的比較
2. 科学的根拠に基づく改善理由
3. 段階的な改善プログラム
4. 簡潔なフィジカル強化メニュー
5. 実戦での確認方法

日本語で、プロレベルの詳細さで回答してください。"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2500,  # トークン数を削減
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                # OpenAI v0.x 対応
                logger.info("OpenAI v0.x APIを使用")
                import openai
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": """あなたは30年以上の経験を持つプロテニスコーチです。世界基準の詳細なアドバイスを日本語で提供してください。"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2500,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"ChatGPT API呼び出しエラー: {e}")
            raise e
    
    def _create_compact_prompt(self, total_score: float, phase_analysis: Dict, basic_advice: Dict) -> str:
        """簡潔なプロンプトを作成（レスポンス切れ問題を解決）"""
        prompt = f"""
【テニスサービス動作解析結果】

総合スコア: {total_score}/10

フェーズ別スコア:
"""
        
        for phase, data in phase_analysis.items():
            score = data.get('score', 0)
            prompt += f"- {phase}: {score}/10\n"
        
        prompt += f"""

基本評価: {basic_advice.get('overall_advice', '')}

【詳細アドバイス要求】

以下の形式で、現在のフォームの問題点と改善方法を提供してください：

## 1. 🏆 総合技術評価
現在のレベルと世界基準での位置づけを評価してください。

## 2. 🔬 バイオメカニクス分析
### 主要改善点（上位3つ）
各部位の現在の角度・位置と理想値を具体的に比較し、改善方法を説明してください。

## 3. 🏅 世界トップ選手比較
フェデラー、ジョコビッチ、ナダルなどとの技術的差異と到達目標を示してください。

## 4. 🎯 8週間改善プログラム
### 第1-2週: 基礎修正期
### 第3-4週: 技術統合期  
### 第5-6週: 実戦応用期
### 第7-8週: 完成期

各期間の具体的な練習内容と目標を簡潔に記載してください。

## 5. 🏋️ 専門フィジカル強化プログラム
### A. 下半身パワー強化（週3回）
• スクワット系: 具体的な重量×回数×セット
• プライオメトリクス: 種目×回数×セット

### B. 体幹安定化（週4回）
• プランク系: 時間×セット
• 回転系: 種目×回数×セット

### C. 上半身連動性（週2回）
• 肩甲骨可動域: 種目×回数×セット
• ローテーターカフ: 重量×回数×セット

## 6. 🧠 メンタル・戦術強化
### A. 集中力向上
• ルーティン確立: 具体的な手順
• 呼吸法: 具体的な方法

### B. 実戦確認システム
練習中のチェックリスト（5項目以内）:
• [ ] 膝角度: 155-165度をキープ
• [ ] 肘高さ: 肩より+8-12cm高い位置
• [ ] トス位置: 前方12-15cm、右側5-8cm
• [ ] 体重移動: 0.3-0.4秒で完了
• [ ] フォロースルー: 体を横切る軌道

各項目は簡潔に、実用的な内容で記載してください。フィジカル強化とメンタル強化は特に簡潔にまとめてください。
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, basic_advice: Dict) -> Dict:
        """AI応答を解析して構造化"""
        try:
            return {
                "summary": basic_advice.get('overall_advice', ''),
                "improvements": basic_advice.get('technical_points', []),
                "drills": basic_advice.get('practice_suggestions', []),
                "enhanced": True,
                "detailed_advice": ai_response
            }
            
        except Exception as e:
            logger.error(f"AI応答解析エラー: {e}")
            basic_advice["enhanced"] = True
            basic_advice["detailed_advice"] = ai_response
            return basic_advice
    
    def _generate_fallback_advice(self) -> Dict:
        """フォールバック用の基本アドバイス"""
        return {
            "summary": "動作解析を完了しました。基本的なフォーム改善から始めましょう。",
            "improvements": [
                "スタンスの安定性を向上させましょう",
                "トスの一貫性を高めましょう",
                "体重移動のタイミングを改善しましょう"
            ],
            "drills": [
                "壁打ちでスタンス練習",
                "トスのみの反復練習",
                "シャドースイング練習"
            ],
            "enhanced": False
        }

def main():
    """テスト用のメイン関数"""
    generator = AdviceGenerator()
    print("AdviceGenerator初期化完了")

if __name__ == "__main__":
    main()

