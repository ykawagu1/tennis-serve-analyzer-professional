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
    
    def generate_advice(self, analysis_data: Dict, user_level: str = 'intermediate', focus_areas: List = None, use_chatgpt: bool = False, api_key: str = '', user_concerns: str = '') -> Dict:
        """
        解析データに基づいてアドバイスを生成（user_concerns対応）
        
        Args:
            analysis_data: 動作解析データ
            user_level: ユーザーレベル
            focus_areas: 重点分野
            use_chatgpt: ChatGPT APIを使用するかどうか
            api_key: OpenAI APIキー
            user_concerns: ユーザーの気になっていること（新機能）
            
        Returns:
            アドバイスデータ
        """
        try:
            logger.info(f"アドバイス生成開始 - ChatGPT使用: {use_chatgpt}, APIキー: {'あり' if (api_key or self.api_key) else 'なし'}, 気になること: {bool(user_concerns)}")
            
            # APIキーの設定（引数で渡された場合は優先）
            if api_key and not self.api_key:
                self.api_key = api_key
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=api_key)
                except ImportError:
                    import openai
                    openai.api_key = api_key
            
            # 基本アドバイスを生成
            basic_advice = self._generate_basic_advice(analysis_data)
            
            if use_chatgpt and (self.api_key or api_key):
                logger.info("ChatGPT詳細アドバイス生成を開始")
                # ChatGPT APIを使用して詳細アドバイスを生成（user_concerns対応）
                enhanced_advice = self._generate_enhanced_advice(analysis_data, basic_advice, user_concerns)
                logger.info(f"ChatGPT詳細アドバイス生成完了 - Enhanced: {enhanced_advice.get('enhanced', False)}")
                return enhanced_advice
            else:
                logger.info("基本アドバイスのみ生成")
                # user_concernsがある場合は基本的なワンポイントアドバイスを追加
                if user_concerns:
                    basic_advice['one_point_advice'] = self._generate_basic_one_point_advice(user_concerns)
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
    
    def _generate_basic_one_point_advice(self, user_concerns: str) -> str:
        """基本的なワンポイントアドバイスを生成"""
        concerns_lower = user_concerns.lower()
        
        if 'トス' in user_concerns:
            return """トスの安定性向上には、以下の3つのポイントが重要です。

1. **一定のリズム**: 毎回同じタイミングでトスを上げる習慣をつけましょう。「1、2、3」のカウントで一定のリズムを作ります。

2. **手首の固定**: トス時に手首を動かさず、肩から腕全体でボールを押し上げるイメージで行います。

3. **目標位置の設定**: 右利きの場合、体の前方12-15cm、右側5-8cmの位置を目標にしてください。

**練習方法**: 毎日トスのみを50回練習し、同じ位置に落ちるよう意識してください。週3回、15分間の集中練習で大幅に改善されます。"""
        
        elif 'フォーム' in user_concerns or 'フォーム' in user_concerns:
            return """フォームの安定化には、基本姿勢の確立が最重要です。

1. **スタンス**: 肩幅程度の足幅で、前足（左足）に体重の60%を乗せます。

2. **上体の角度**: 軽く前傾姿勢を保ち、肩の力を抜いてリラックスします。

3. **ラケットの構え**: ラケットヘッドを立て、グリップは軽く握ります。

**練習方法**: 鏡の前でのシャドースイング（週4回、各10分）と、動画撮影による自己チェック（週1回）を行ってください。正しいフォームの習得には約4-6週間必要です。"""
        
        elif 'パワー' in user_concerns or '威力' in user_concerns:
            return """サーブのパワー向上には、体全体の連動性が鍵となります。

1. **下半身の活用**: 膝の曲げ伸ばしを使って、地面からの力を上半身に伝えます。

2. **体幹の回転**: 腰から肩にかけての回転運動で、ラケットスピードを最大化します。

3. **インパクトタイミング**: 体重移動の完了と同時にインパクトを迎えるよう調整します。

**練習方法**: プライオメトリクス（ジャンプ系）トレーニングを週3回、体幹回転ドリルを週4回実施してください。2-3週間で明確な改善を実感できます。"""
        
        elif 'コントロール' in user_concerns or '精度' in user_concerns or 'コントロール' in user_concerns:
            return """サーブの精度向上には、再現性の高いフォーム作りが重要です。

1. **ターゲット設定**: 練習時は必ず具体的なターゲット（コーンなど）を設置します。

2. **フォロースルーの一貫性**: 毎回同じ軌道でフォロースルーを行い、ラケット面の向きを安定させます。

3. **リズムの統一**: サービスルーティンを決めて、毎回同じリズムで実行します。

**練習方法**: 近距離（サービスライン）からのコントロール練習を週5回、各30球実施してください。成功率70%を目標に、段階的に距離を伸ばします。"""
        
        else:
            return """あなたの悩みに対する総合的なアドバイスです。

1. **基礎の確認**: まずは基本的なグリップ、スタンス、トスの確認から始めましょう。

2. **段階的改善**: 一度に全てを変えず、週単位で1つずつポイントを改善していきます。

3. **継続的練習**: 毎日15-20分の基礎練習を継続することで、確実な改善が期待できます。

**練習方法**: 基本動作の反復練習（週6回、各15分）と、月1回の動画チェックで進捗を確認してください。改善には個人差がありますが、通常4-8週間で明確な変化を実感できます。"""
    
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
                
                # user_concernsがある場合はワンポイントアドバイスを抽出
                if user_concerns:
                    enhanced_advice["one_point_advice"] = self._extract_one_point_advice(ai_response, user_concerns)
                
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
            # user_concernsがある場合は基本的なワンポイントアドバイスを追加
            if user_concerns:
                basic_advice['one_point_advice'] = self._generate_basic_one_point_advice(user_concerns)
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

テニスサービスの動作解析結果に基づいて、世界基準の詳細なアドバイスを提供してください。特にユーザーの具体的な悩みがある場合は、その悩みに特化したワンポイントアドバイスも含めてください。

以下の形式で回答してください：

1. 現在のフォームと理想フォームの具体的比較
2. 科学的根拠に基づく改善理由
3. 段階的な改善プログラム
4. 簡潔なフィジカル強化メニュー
5. 実戦での確認方法
6. （ユーザーの悩みがある場合）その悩みに特化したワンポイントアドバイス

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
    
    def _create_compact_prompt(self, total_score: float, phase_analysis: Dict, basic_advice: Dict, user_concerns: str = '') -> str:
        """簡潔なプロンプトを作成（user_concerns対応）"""
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

        # user_concernsがある場合は追加
        if user_concerns:
            prompt += f"""
【ユーザーの気になっていること】
{user_concerns}
"""

        prompt += f"""

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
• スクワット系、プライオメトリクス等を簡潔に

### B. 体幹安定化（週4回）
• プランク系、回転系等を簡潔に

### C. 上半身連動性（週2回）
• 肩甲骨可動域、ローテーターカフ等を簡潔に

## 6. 🧠 メンタル・戦術強化
### A. 集中力向上
• ルーティン確立、呼吸法等を簡潔に

### B. 実戦確認システム
練習中のチェックリスト（5項目以内）を簡潔に
"""

        # user_concernsがある場合は専用セクションを追加
        if user_concerns:
            prompt += f"""

## 7. 💡 あなたへのワンポイントアドバイス
「{user_concerns}」について、500文字程度で以下を含めて回答してください：
- 問題の原因分析
- 具体的な改善方法
- 推奨練習メニューと頻度
- 改善までの期間目安
"""

        prompt += """

各項目は簡潔に、実用的な内容で記載してください。フィジカル強化とメンタル強化は特に簡潔にまとめてください。
"""
        
        return prompt
    
    def _extract_one_point_advice(self, ai_response: str, user_concerns: str) -> str:
        """AI応答からワンポイントアドバイスを抽出"""
        try:
            # "あなたへのワンポイントアドバイス"セクションを探す
            lines = ai_response.split('\n')
            in_one_point_section = False
            one_point_lines = []
            
            for line in lines:
                if '💡' in line and ('ワンポイント' in line or 'ポイント' in line):
                    in_one_point_section = True
                    continue
                elif line.startswith('##') and in_one_point_section:
                    break
                elif in_one_point_section and line.strip():
                    one_point_lines.append(line.strip())
            
            if one_point_lines:
                return '\n'.join(one_point_lines)
            else:
                # セクションが見つからない場合は基本的なアドバイスを生成
                return self._generate_basic_one_point_advice(user_concerns)
                
        except Exception as e:
            logger.error(f"ワンポイントアドバイス抽出エラー: {e}")
            return self._generate_basic_one_point_advice(user_concerns)
    
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

