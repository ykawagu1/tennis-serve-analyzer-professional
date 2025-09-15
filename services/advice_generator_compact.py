import logging
from typing import Dict, List, Optional

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
    
    def generate_advice(self, analysis_data: Dict, user_level: str = 'intermediate', focus_areas: List[str] = None, use_chatgpt: bool = False, api_key: str = '', user_concerns: str = '') -> Dict:
        """
        解析データに基づいてアドバイスを生成
        
        Args:
            analysis_data: 動作解析データ
            user_level: ユーザーレベル
            focus_areas: 重点分野
            use_chatgpt: ChatGPT APIを使用するかどうか
            api_key: OpenAI APIキー
            user_concerns: ユーザーの気になっていること
            
        Returns:
            アドバイスデータ
        """
        try:
            logger.info(f"=== アドバイス生成開始 ===")
            logger.info(f"ChatGPT使用: {use_chatgpt}")
            logger.info(f"APIキー: {'あり' if self.api_key else 'なし'}")
            logger.info(f"ユーザーの悩み: {user_concerns}")
            logger.info(f"analysis_data keys: {list(analysis_data.keys()) if analysis_data else 'None'}")
            logger.info(f"analysis_data type: {type(analysis_data)}")
            
            # 基本アドバイスを生成
            logger.info("基本アドバイス生成を開始")
            basic_advice = self._generate_basic_advice(analysis_data)
            logger.info(f"基本アドバイス生成完了: {type(basic_advice)}")
            logger.info(f"basic_advice keys: {list(basic_advice.keys()) if basic_advice else 'None'}")
            
            if use_chatgpt and (self.api_key or api_key):
                logger.info("ChatGPT詳細アドバイス生成を開始")
                # APIキーが引数で渡された場合は更新
                if api_key and not self.api_key:
                    self.api_key = api_key
                    try:
                        from openai import OpenAI
                        self.client = OpenAI(api_key=api_key)
                    except ImportError:
                        pass
                
                # ChatGPT APIを使用して詳細アドバイスを生成（user_concerns対応）
                enhanced_advice = self._generate_enhanced_advice(analysis_data, basic_advice, user_concerns)
                logger.info(f"ChatGPT詳細アドバイス生成完了 - Enhanced: {enhanced_advice.get('enhanced', False)}")
                return enhanced_advice
            else:
                logger.info("基本アドバイスのみ生成")
                # user_concernsがある場合は基本アドバイスに追加
                if user_concerns:
                    concerns_advice = self._generate_basic_concerns_advice(user_concerns)
                    # detailed_adviceに気になっていることのアドバイスを追加
                    basic_advice['detailed_advice'] += f"""

## あなたの気になっていることについて
**「{user_concerns}」について**

{concerns_advice}
"""
                return basic_advice
                
        except Exception as e:
            logger.error(f"アドバイス生成エラー: {e}")
            logger.error(f"エラータイプ: {type(e).__name__}")
            logger.error(f"エラー詳細: {str(e)}")
            import traceback
            logger.error(f"スタックトレース: {traceback.format_exc()}")
            return self._generate_fallback_advice()
    
    def _generate_basic_advice(self, analysis_data: Dict) -> Dict:
        """基本的なアドバイスを生成"""
        logger.info(f"=== _generate_basic_advice 開始 ===")
        logger.info(f"analysis_data: {analysis_data}")
        
        total_score = analysis_data.get('total_score', 0)
        phase_analysis = analysis_data.get('phase_analysis', {})
        
        logger.info(f"total_score: {total_score}")
        logger.info(f"phase_analysis: {phase_analysis}")
        
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
        
        # 基本アドバイスをdetailed_advice形式に変換
        detailed_advice = f"""## 総合評価
{overall}

## 技術的改善ポイント
"""
        for i, point in enumerate(technical_points[:5], 1):
            detailed_advice += f"{i}. {point}\n"
        
        detailed_advice += f"""
## 練習提案
"""
        for i, suggestion in enumerate(practice_suggestions[:5], 1):
            detailed_advice += f"{i}. {suggestion}\n"
        
        return {
            "overall_advice": overall,
            "technical_points": technical_points[:5],  # 最大5つ
            "practice_suggestions": practice_suggestions[:5],  # 最大5つ
            "enhanced": False,
            "detailed_advice": detailed_advice  # フロントエンド用に追加
            # errorキーは設定しない（ChatGPT使用時のみ設定）
        }
    
    def _generate_enhanced_advice(self, analysis_data: Dict, basic_advice: Dict, user_concerns: str = '') -> Dict:
        """ChatGPT APIを使用して詳細なアドバイスを生成（user_concerns対応）"""
        try:
            logger.info("ChatGPT API呼び出し開始")
            
            # 解析データを整理
            total_score = analysis_data.get('total_score', 0)
            phase_analysis = analysis_data.get('phase_analysis', {})
            
            # ChatGPTへの簡潔なプロンプトを作成（user_concerns対応）
            prompt = self._create_compact_prompt(total_score, phase_analysis, basic_advice, user_concerns)
            
            # ChatGPT APIを呼び出し
            ai_response = self._call_chatgpt_api(prompt)
            
            if ai_response:
                logger.info("ChatGPT API呼び出し成功")
                # レスポンスを解析
                enhanced_advice = self._parse_ai_response(ai_response, basic_advice)
                enhanced_advice["enhanced"] = True
                enhanced_advice["detailed_advice"] = ai_response
                enhanced_advice["user_concerns"] = user_concerns
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
                    model="gpt-4.1-nano",  # GPT-4.1 nanoを使用
                    messages=[
                        {
                            "role": "system",
                            "content": """あなたは30年以上の経験を持つATP/WTAツアーのプロテニスコーチです。グランドスラム優勝者を指導した実績があり、スポーツ科学博士号（バイオメカニクス専門）を持っています。

テニスサービスの動作解析結果に基づいて、詳細なアドバイスを提供してください。以下の形式で回答してください：

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
                    model="gpt-4.1-nano",
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
                    max_tokens=5000,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"ChatGPT API呼び出しエラー: {e}")
            raise e
    
    def _create_compact_prompt(self, total_score: float, phase_analysis: Dict, basic_advice: Dict, user_concerns: str = '') -> str:
        """簡潔なプロンプトを作成（レスポンス切れ問題を解決、user_concerns対応）"""
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
"""

        # ユーザーの悩みがある場合は追加
        if user_concerns:
            prompt += f"""
【ユーザーの気になっていること】
{user_concerns}

上記の悩みに対する具体的なアドバイスも含めて回答してください。
"""

        prompt += f"""

【詳細アドバイス要求】

以下の形式で、現在のフォームの問題点と改善方法を提供してください：

## 1. 🏆 総合技術評価
現在のレベルをアマチュア上級者と比較して評価してください。

## 2. 🔬 バイオメカニクス分析
### 主要改善点（上位５つ）
各部位の現在の角度・位置と理想値を具体的に比較し、改善方法をそれぞれ２００文字程度で説明してください。
（例）スタンスの広さ
（例）肘の位置、高さ
（例）膝の曲げ角度
（例）手首の使い方
（例）フォロースルーの姿勢
（例）体幹の捻り方
## 3. 🏅 世界トップ選手比較
フェデラー、ジョコビッチ、ナダルなどとの技術的差異と到達目標を示してください。

## 4. 🎯 8週間改善プログラム
### 第1-2週: 基礎修正期
### 第3-4週: 技術統合期  
### 第5-6週: 実戦応用期
### 第7-8週: 完成期

各期間の具体的な練習内容と目標をそれぞれ２００文字程度で記載してください。その際、情報があれば、性別、体格、身長、体重、年齢も加味してください。

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
"""

        # ユーザーの悩みがある場合は専用セクションを追加
        if user_concerns:
            prompt += f"""

## 7. 💡 あなたへのワンポイントアドバイス
「{user_concerns}」について、具体的な改善方法とトレーニング方法を500文字程度で詳しく説明してください。
"""

        prompt += """
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
        detailed_advice = """## 総合評価
動作解析を完了しました。基本的なフォーム改善から始めましょう。

## 技術的改善ポイント
1. スタンスの安定性を向上させましょう
2. トスの一貫性を高めましょう
3. 体重移動のタイミングを改善しましょう

## 練習提案
1. 壁打ちでスタンス練習
2. トスのみの反復練習
3. シャドースイング練習
"""
        
        return {
            "overall_advice": "動作解析を完了しました。基本的なフォーム改善から始めましょう。",
            "technical_points": [
                "スタンスの安定性を向上させましょう",
                "トスの一貫性を高めましょう",
                "体重移動のタイミングを改善しましょう"
            ],
            "practice_suggestions": [
                "壁打ちでスタンス練習",
                "トスのみの反復練習",
                "シャドースイング練習"
            ],
            "enhanced": False,
            "detailed_advice": detailed_advice,
            "error": "解析処理中にエラーが発生しましたが、基本アドバイスを提供します。"
        }

def main():
    """テスト用のメイン関数"""
    generator = AdviceGenerator()
    print("AdviceGenerator初期化完了")

if __name__ == "__main__":
    main()


    def _generate_basic_concerns_advice(self, user_concerns: str) -> str:
        """ユーザーの悩みに対する基本的なアドバイスを生成"""
        concerns_lower = user_concerns.lower()
        
        if 'トス' in concerns_lower:
            return """トスの安定性向上には、以下の3つのポイントが重要です：
1. 毎回同じ位置でボールをリリースする（肩の真上より少し前方）
2. 手首を固定し、腕全体でボールを上げる
3. 毎日50回のトス練習を継続する
改善期間：2-3週間で効果を実感できます。"""
        
        elif 'フォーム' in concerns_lower:
            return """フォームの安定化には、基本姿勢の確立が重要です：
1. スタンスを肩幅に保ち、体重を前足に乗せる
2. ラケットの軌道を一定にするため、シャドースイング練習
3. 鏡の前でフォームチェックを毎日実施
改善期間：4-6週間で基本フォームが安定します。"""
        
        elif 'パワー' in concerns_lower:
            return """サーブパワー向上には、体全体の連動が重要です：
1. 下半身から上半身への体重移動を意識
2. 体幹の回転力を活用したスイング
3. 週3回の筋力トレーニング（スクワット、プランク）
改善期間：6-8週間でパワーアップを実感できます。"""
        
        elif '精度' in concerns_lower or 'コントロール' in concerns_lower:
            return """サーブ精度向上には、一貫性のある動作が重要です：
1. 毎回同じリズムでサーブを打つ
2. ターゲットを決めて集中練習
3. フォロースルーを最後まで完了させる
改善期間：3-4週間で精度向上を実感できます。"""
        
        else:
            return f"""「{user_concerns}」の改善には、基本動作の見直しが重要です：
1. 現在のフォームを動画で確認し、問題点を特定
2. 一つずつ段階的に修正していく
3. 継続的な練習と定期的なフォームチェック
改善期間：個人差がありますが、4-6週間で変化を実感できます。"""

