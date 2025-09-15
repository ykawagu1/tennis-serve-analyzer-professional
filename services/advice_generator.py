import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AdviceGenerator:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.client = None
        if self.api_key:
            self._init_openai_client(self.api_key)
        else:
            logger.warning("OpenAI APIキーが環境変数にセットされていません")

    def _init_openai_client(self, api_key: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI クライアント初期化成功（v1.0+）")
        except ImportError:
            try:
                import openai
                openai.api_key = api_key
                logger.info("OpenAI API キー設定成功（v0.x）")
            except ImportError:
                logger.error("OpenAI ライブラリがインストールされていません")

    def generate_advice(
        self,
        analysis_data: Dict,
        user_level: str = 'intermediate',
        focus_areas: List = None,
        use_chatgpt: Optional[bool] = False,
        user_concerns: str = '',
        language: str = 'ja'
    ) -> Dict:
        logger.info(f"アドバイス生成開始 - ChatGPT使用: {use_chatgpt}, 気になること: {bool(user_concerns)}")
        basic_advice = self._generate_basic_advice(analysis_data, language=language)

        if use_chatgpt and self.api_key:
            try:
                logger.info("ChatGPT詳細アドバイス生成開始")
                enhanced_advice = self._generate_enhanced_advice(
                    analysis_data, basic_advice, user_concerns, language=language)
                logger.info(f"ChatGPT詳細アドバイス生成完了 - Enhanced: {enhanced_advice.get('enhanced', False)}")
                return enhanced_advice
            except Exception as e:
                logger.error(f"ChatGPT API呼び出しエラー: {e}")
                basic_advice["enhanced"] = False
                basic_advice["error"] = f"ChatGPT接続エラー: {str(e)}"
                if user_concerns:
                    basic_advice['one_point_advice'] = self._generate_basic_one_point_advice(user_concerns)
                return basic_advice
        else:
            logger.info("無料枠なので詳細アドバイスは生成されません")
            if user_concerns:
                basic_advice['one_point_advice'] = self._generate_basic_one_point_advice(user_concerns)
            basic_advice['error'] = '有料プランのみAI詳細アドバイスを利用できます。'
            return basic_advice

    def _generate_basic_advice(self, analysis_data: Dict, language: str = 'en') -> Dict:
        # 総合評価メッセージ
        BASIC_ADVICE_MESSAGES = {
            'ja': [
                "素晴らしいサーブフォームです！細かな調整でさらに上達できます。",
                "良いサーブフォームです。いくつか改善点があります。",
                "基本のフォームはできています。重要なポイントを強化しましょう。",
                "改善の余地がたくさんあります。基礎から見直しましょう。"
            ],
            'en': [
                "Excellent service form! With minor adjustments, you can improve even further.",
                "Good service form. There are a few points to improve.",
                "The basic form is there. Let's work on the key areas.",
                "There's plenty of room for improvement. Let's review the basics."
            ],
            'es': [
                "¡Excelente forma de saque! Con pequeños ajustes, puedes mejorar aún más.",
                "Buena forma de saque. Hay algunos puntos por mejorar.",
                "La forma básica está lograda. Trabajemos en los aspectos clave.",
                "Hay mucho margen de mejora. Repasemos los conceptos básicos."
            ],
            'pt': [
                "Excelente forma de saque! Com pequenos ajustes, você pode melhorar ainda mais.",
                "Boa forma de saque. Há alguns pontos a melhorar.",
                "A forma básica está presente. Vamos trabalhar nos pontos principais.",
                "Há muito espaço para melhoria. Vamos revisar o básico."
            ],
            'fr': [
                "Excellente forme de service ! Avec quelques ajustements, vous pouvez encore progresser.",
                "Bonne forme de service. Quelques points à améliorer.",
                "La forme de base est présente. Travaillons les points clés.",
                "Il y a beaucoup de marge de progression. Reprenons les bases."
            ],
            'de': [
                "Ausgezeichnete Aufschlagtechnik! Mit kleinen Anpassungen kannst du noch besser werden.",
                "Gute Aufschlagtechnik. Es gibt einige Punkte zu verbessern.",
                "Die Grundform stimmt. Lass uns an den wichtigsten Punkten arbeiten.",
                "Es gibt viel Verbesserungspotenzial. Gehen wir die Grundlagen noch einmal durch."
            ]
        }

        # Phaseごとの多言語アドバイス辞書
        PHASE_DETAILS = {
            "preparation": {
                "advice": {
                    'ja': "スタンス（足の位置）の安定性を高めましょう。",
                    'en': "Improve the stability of your stance (foot positioning).",
                    'es': "Mejora la estabilidad de tu postura (posición de los pies).",
                    'pt': "Melhore a estabilidade da sua posição (posicionamento dos pés).",
                    'fr': "Améliorez la stabilité de votre position (placement des pieds).",
                    'de': "Verbessere die Stabilität deines Stands (Fußpositionierung)."
                },
                "suggestion": {
                    'ja': "壁に向かって正しいスタンスでシャドースイング練習をしましょう。",
                    'en': "Practice shadow swings with the correct stance against a wall.",
                    'es': "Practica swings al aire con la postura correcta frente a una pared.",
                    'pt': "Pratique swings no ar com a postura correta em frente à parede.",
                    'fr': "Entraînez-vous à faire des swings à vide avec la bonne position face à un mur.",
                    'de': "Übe Schattenaufschläge mit korrektem Stand vor einer Wand."
                }
            },
            "ball_toss": {
                "advice": {
                    'ja': "トスの高さと位置の安定性を高めましょう。",
                    'en': "Improve the consistency of your toss height and position.",
                    'es': "Mejora la consistencia de la altura y posición del lanzamiento.",
                    'pt': "Melhore a consistência da altura e posição do lançamento.",
                    'fr': "Améliorez la régularité de la hauteur et de la position du lancer.",
                    'de': "Verbessere die Konstanz der Wurfhöhe und -position."
                },
                "suggestion": {
                    'ja': "毎回同じ高さにトスできるように反復練習しましょう。",
                    'en': "Repeat tossing the ball to the same height for consistency.",
                    'es': "Repite el lanzamiento de la pelota a la misma altura para mayor consistencia.",
                    'pt': "Repita o lançamento da bola sempre na mesma altura para maior consistência.",
                    'fr': "Répétez le lancer à la même hauteur pour plus de régularité.",
                    'de': "Wiederhole den Ballwurf immer auf die gleiche Höhe für mehr Konstanz."
                }
            },
            "trophy_position": {
                "advice": {
                    'ja': "トロフィーポジションをマスターして安定した力を生み出しましょう。",
                    'en': "Master the trophy position to build power and consistency.",
                    'es': "Domina la posición de trofeo para ganar potencia y regularidad.",
                    'pt': "Domine a posição de troféu para obter força e consistência.",
                    'fr': "Maîtrisez la position trophy pour gagner en puissance et en régularité.",
                    'de': "Beherrsche die Trophy-Position für mehr Kraft und Konstanz."
                },
                "suggestion": {
                    'ja': "シャドースイング時にトロフィーポジションで一旦静止して確認しましょう。",
                    'en': "Pause and check your trophy position during shadow swings.",
                    'es': "Haz una pausa en la posición de trofeo al practicar swings al aire.",
                    'pt': "Pare e confira a posição de troféu durante os swings no ar.",
                    'fr': "Faites une pause dans la position trophy lors de swings à vide.",
                    'de': "Halte bei Schattenaufschlägen kurz in der Trophy-Position an."
                }
            },
            "acceleration": {
                "advice": {
                    'ja': "スイングスピードと軌道を最適化しましょう。",
                    'en': "Optimize your swing speed and trajectory.",
                    'es': "Optimiza la velocidad y trayectoria de tu swing.",
                    'pt': "Otimize a velocidade e a trajetória do seu swing.",
                    'fr': "Optimisez la vitesse et la trajectoire de votre swing.",
                    'de': "Optimiere Schwunggeschwindigkeit und -bahn."
                },
                "suggestion": {
                    'ja': "練習スイングで徐々にスピードを上げてみましょう。",
                    'en': "Gradually increase swing speed during practice swings.",
                    'es': "Aumenta gradualmente la velocidad del swing en la práctica.",
                    'pt': "Aumente gradualmente a velocidade do swing durante os treinos.",
                    'fr': "Augmentez progressivement la vitesse du swing à l’entraînement.",
                    'de': "Steigere die Schwunggeschwindigkeit bei Übungsschlägen allmählich."
                }
            },
            "contact": {
                "advice": {
                    'ja': "インパクトポイントを安定させましょう。",
                    'en': "Improve your contact point with the ball.",
                    'es': "Mejora el punto de contacto con la pelota.",
                    'pt': "Melhore o ponto de contato com a bola.",
                    'fr': "Améliorez le point de contact avec la balle.",
                    'de': "Verbessere den Treffpunkt mit dem Ball."
                },
                "suggestion": {
                    'ja': "ネット前でインパクトポイントを確認する練習をしましょう。",
                    'en': "Practice checking the contact point in front of the net.",
                    'es': "Practica comprobando el punto de contacto delante de la red.",
                    'pt': "Pratique verificando o ponto de contato em frente à rede.",
                    'fr': "Entraînez-vous à vérifier le point de contact devant le filet.",
                    'de': "Übe, den Treffpunkt vor dem Netz zu kontrollieren."
                }
            },
            "follow_through": {
                "advice": {
                    'ja': "フォロースルー（振り抜き）の安定性を高めましょう。",
                    'en': "Stabilize your finish (follow-through) position.",
                    'es': "Estabiliza la posición final del swing (follow-through).",
                    'pt': "Estabilize a posição final do swing (follow-through).",
                    'fr': "Stabilisez la position de finition (follow-through).",
                    'de': "Stabilisiere deine Endposition (Ausschwung)."
                },
                "suggestion": {
                    'ja': "スローモーションでフォロースルーに意識して練習しましょう。",
                    'en': "Focus on the follow-through in slow-motion practice swings.",
                    'es': "Concéntrate en el follow-through en swings en cámara lenta.",
                    'pt': "Foque no follow-through durante swings em câmera lenta.",
                    'fr': "Concentrez-vous sur le follow-through lors de swings au ralenti.",
                    'de': "Achte bei Übungsschlägen in Zeitlupe besonders auf den Ausschwung."
                }
            }
        }

        # 言語フォールバック
        lang = language if language in BASIC_ADVICE_MESSAGES else 'en'

        # スコアでメッセージIndex決定
        total_score = (
            analysis_data.get('total_score')
            or analysis_data.get('tiered_evaluation', {}).get('total_score')
            or analysis_data.get('overall_score')
            or 0
        )
        if total_score >= 8:
            idx = 0
        elif total_score >= 6:
            idx = 1
        elif total_score >= 4:
            idx = 2
        else:
            idx = 3
        overall = BASIC_ADVICE_MESSAGES[lang][idx]

        phase_analysis = analysis_data.get('phase_analysis', {})
        technical_points = []
        practice_suggestions = []

        for phase, data in phase_analysis.items():
            score = data.get('score', 0) if isinstance(data, dict) else 0
            if score < 7:
                details = PHASE_DETAILS.get(phase)
                if details:
                    technical_points.append(details["advice"][lang])
                    practice_suggestions.append(details["suggestion"][lang])
                else:
                    print(f"WARNING: Phase {phase} not localized for language {lang}")

        return {
            "basic_advice": overall,
            "technical_points": technical_points,
            "practice_suggestions": practice_suggestions,
            "enhanced": False
        }

    def _generate_enhanced_advice(self, analysis_data: Dict, basic_advice: Dict, user_concerns: str = '', language: str = 'ja') -> Dict:
        total_score = analysis_data.get('total_score', 0)
        phase_analysis = analysis_data.get('phase_analysis', {})

        prompt = self._create_detailed_prompt(total_score, phase_analysis, basic_advice, user_concerns, language=language)
        ai_response = self._call_chatgpt_api(prompt, language=language)
        if ai_response:
            logger.info("ChatGPT API呼び出し成功")
            enhanced_advice = self._parse_ai_response(ai_response, basic_advice)
            enhanced_advice["enhanced"] = True
            enhanced_advice["detailed_advice"] = ai_response
            enhanced_advice["enhanced_advice"] = ai_response
            if user_concerns:
                enhanced_advice["one_point_advice"] = self._extract_one_point_advice(ai_response, user_concerns)
            return enhanced_advice
        else:
            logger.error("ChatGPT APIからの応答が空です")
            basic_advice["enhanced"] = False
            basic_advice["error"] = "ChatGPT APIからの応答が空でした"
            return basic_advice

    # 以下はもともとのコードをインデント・構文エラーなしで再掲
    def _create_detailed_prompt(
        self, total_score: float, phase_analysis: Dict, basic_advice: Dict, user_concerns: str = '', language: str = 'ja'
    ) -> str:
        phase_scores = []
        weak_phases = []
        for phase, data in phase_analysis.items():
            score = data.get('score', 0) if isinstance(data, dict) else 0
            phase_scores.append(f"{phase}: {score:.1f}")
            if score < 7:
                weak_phases.append(phase)

        # concerns_text 多言語分岐
        concerns_text = ""
        if user_concerns:
            if language == "ja":
                concerns_text = f"\n\n【ユーザーの具体的な悩み】\n{user_concerns}\n\n上記の悩みに特に焦点を当てて、具体的で実践的なアドバイスを含めてください。"
            elif language == "en":
                concerns_text = f"\n\n[User's specific concern(s)]\n{user_concerns}\n\nFocus on the above concern(s) and include concrete, practical advice."
            elif language == "es":
                concerns_text = f"\n\n[Inquietud(es) específica(s) del usuario]\n{user_concerns}\n\nEnfócate en la(s) inquietud(es) mencionada(s) e incluye consejos concretos y prácticos."
            elif language == "pt":
                concerns_text = f"\n\n[Preocupação(ões) específica(s) do usuário]\n{user_concerns}\n\nFoque nas preocupações acima e inclua conselhos concretos e práticos."
            elif language == "fr":
                concerns_text = f"\n\n[Préoccupation(s) spécifique(s) de l'utilisateur]\n{user_concerns}\n\nConcentrez-vous sur les préoccupations ci-dessus et incluez des conseils concrets et pratiques."
            elif language == "de":
                concerns_text = f"\n\n[Spezifische(r) Benutzeranliegen]\n{user_concerns}\n\nKonzentrieren Sie sich auf das/die oben genannte(n) Anliegen und geben Sie konkrete, praktische Ratschläge."
        if language == "ja":
            prompt = f"""【テニスサーブ動作解析結果】

総合スコア: {total_score:.1f}/10点

フェーズ別スコア:
{chr(10).join(phase_scores)}

改善が必要なフェーズ: {', '.join(weak_phases) if weak_phases else 'なし'}

基本的な技術ポイント:
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

この解析結果に基づいて、以下の構成で詳細なアドバイスを生成してください：
・（500文字程度）といった表現は絶対に表示しないでください。また箇条書きにして明確に記載してください。
1. フォーム改善点の詳細分析
2. 4週間トレーニングプログラム
3. フィジカル強化メニュー
4. 実戦での確認ポイント
5. ワンポイントアドバイス

特に改善が必要なフェーズ（{', '.join(weak_phases)}）に重点を置いて、具体的で実践的なアドバイスをお願いします。
【アドバイス生成要件】
・各項目で悩みに必ず言及し、一般論だけで済ませないこと。
・悩みが曖昧でも「考えられる理由」と「改善案」を必ず入れること。
・直接、テニスに関係ない悩みにも、共感と改善案を必ず入れること。
"""
        elif language == "en":
            prompt = f"""[Tennis Serve Analysis Result]

Overall score: {total_score:.1f}/10

Phase-by-phase scores:
{chr(10).join(phase_scores)}

Phases needing improvement: {', '.join(weak_phases) if weak_phases else 'None'}

Key technical points:
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

Based on this analysis, please generate a detailed and actionable coaching report with the following structure (do **not** write any length restrictions):
1. Detailed analysis of form improvements
2. 4-week training program
3. Physical strengthening plan
4. Key points for match play
5. One-point advice

Focus especially on the phases needing improvement ({', '.join(weak_phases)}) and ensure all advice is specific and practical for the user's level and concern(s).

[Coaching requirements]
- Address the user's concern(s) directly in each section.
- Even if the concern is vague, include likely reasons and practical solutions.
- If the concern is not tennis-related, include empathy and advice for that topic as well.
"""
        elif language == "es":
            prompt = f"""
[Tennis Serve Analysis Result]

Puntuación total: {total_score:.1f}/10

Puntuación por fases:
{chr(10).join(phase_scores)}

Fases que requieren mejora: {', '.join(weak_phases) if weak_phases else 'Ninguna'}

Puntos técnicos clave:
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

Con base en este análisis, genera un informe detallado de coaching siguiendo esta estructura (no escribas restricciones de longitud):
1. Análisis detallado de las mejoras de técnica
2. Programa de entrenamiento de 4 semanas
3. Plan de fortalecimiento físico
4. Puntos clave para partidos
5. Consejo de un solo punto

Enfócate especialmente en las fases que requieren mejora ({', '.join(weak_phases)}) y asegúrate de que todo el consejo sea específico y práctico para el nivel y las inquietudes del usuario.

[Requisitos de coaching]
- Aborda directamente las inquietudes del usuario en cada sección.
- Incluso si la inquietud es vaga, incluye posibles razones y soluciones prácticas.
- Si la inquietud no está relacionada con el tenis, incluye empatía y consejos también para ese tema.
"""
        elif language == "pt":
            prompt = f"""
[Resultado da Análise do Saque de Tênis]

Pontuação geral: {total_score:.1f}/10

Pontuações por fase:
{chr(10).join(phase_scores)}

Fases que precisam de melhoria: {', '.join(weak_phases) if weak_phases else 'Nenhuma'}

Pontos técnicos principais:
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

Com base nesta análise, gere um relatório detalhado de coaching com a seguinte estrutura (não escreva restrições de tamanho):
1. Análise detalhada dos pontos de melhoria da técnica
2. Programa de treinamento de 4 semanas
3. Plano de fortalecimento físico
4. Pontos principais para jogos
5. Dica pontual

Dê especial atenção às fases que precisam de melhoria ({', '.join(weak_phases)}) e garanta que todos os conselhos sejam específicos e práticos para o nível e as preocupações do usuário.

[Requisitos de coaching]
- Aborde diretamente as preocupações do usuário em cada seção.
- Mesmo que a preocupação seja vaga, inclua possíveis razões e soluções práticas.
- Se a preocupação não for relacionada ao tênis, inclua empatia e conselhos também para esse tema.
"""
        elif language == "fr":
            prompt = f"""
[Résultat de l'analyse du service de tennis]

Score global : {total_score:.1f}/10

Scores par phase :
{chr(10).join(phase_scores)}

Phases nécessitant des améliorations : {', '.join(weak_phases) if weak_phases else 'Aucune'}

Points techniques clés :
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

Sur la base de cette analyse, veuillez générer un rapport d'entraînement détaillé avec la structure suivante (n'indiquez aucune restriction de longueur) :
1. Analyse détaillée des axes d'amélioration de la technique
2. Programme d'entraînement sur 4 semaines
3. Plan de renforcement physique
4. Points clés pour les matchs
5. Conseil unique

Mettez particulièrement l'accent sur les phases nécessitant des améliorations ({', '.join(weak_phases)}) et assurez-vous que tous les conseils soient spécifiques et pratiques pour le niveau et les préoccupations de l'utilisateur.

[Exigences de coaching]
- Traitez directement les préoccupations de l'utilisateur dans chaque section.
- Même si la préoccupation est vague, incluez des raisons possibles et des solutions pratiques.
- Si la préoccupation n'est pas liée au tennis, incluez également de l'empathie et des conseils pour ce sujet.
"""
        elif language == "de":
            prompt = f"""
[Ergebnis der Tennis-Aufschlag-Analyse]

Gesamtpunktzahl: {total_score:.1f}/10

Punkte nach Phasen:
{chr(10).join(phase_scores)}

Phasen, die verbessert werden müssen: {', '.join(weak_phases) if weak_phases else 'Keine'}

Wichtige technische Punkte:
{chr(10).join(f"- {point}" for point in basic_advice.get('technical_points', []))}
{concerns_text}

Basierend auf dieser Analyse erstellen Sie bitte einen detaillierten und umsetzbaren Coaching-Bericht mit folgender Struktur (geben Sie keine Längenbeschränkungen an):
1. Detaillierte Analyse der Verbesserungsmöglichkeiten der Technik
2. 4-Wochen-Trainingsprogramm
3. Plan zur körperlichen Stärkung
4. Wichtige Punkte für Matches
5. Ein-Punkt-Ratschlag

Konzentrieren Sie sich besonders auf die Phasen, die verbessert werden müssen ({', '.join(weak_phases)}), und stellen Sie sicher, dass alle Ratschläge spezifisch und praktisch für das Niveau und die Anliegen des Nutzers sind.

[Coaching-Anforderungen]
- Gehen Sie in jedem Abschnitt direkt auf die Anliegen des Nutzers ein.
- Auch wenn das Anliegen vage ist, geben Sie wahrscheinliche Gründe und praktische Lösungen an.
- Ist das Anliegen nicht tennisbezogen, geben Sie auch dafür Empathie und Ratschläge.
"""
        else:
            prompt = "(多言語分岐を書く)"
        return prompt

    def _parse_ai_response(self, ai_response: str, basic_advice: Dict) -> Dict:
        enhanced_advice = basic_advice.copy()
        enhanced_advice["detailed_advice"] = ai_response
        enhanced_advice["enhanced"] = True
        return enhanced_advice

    def _extract_one_point_advice(self, ai_response: str, user_concerns: str) -> str:
        lines = ai_response.split('\n')
        one_point_section = False
        one_point_advice = []
        for line in lines:
            if 'ワンポイント' in line or '即効性' in line or 'One-point' in line or 'Quick tip' in line:
                one_point_section = True
                continue
            elif one_point_section and line.strip():
                # セクション区切り（#や数字始まりなど）で終了
                if (line.startswith('#') or line.strip().startswith('1.')) and 'ワンポイント' not in line and 'One-point' not in line:
                    break
                one_point_advice.append(line.strip())
        if one_point_advice:
            return '\n'.join(one_point_advice)
        else:
            return self._generate_basic_one_point_advice(user_concerns)

    def _generate_basic_one_point_advice(self, user_concerns: str) -> str:
        concerns_lower = user_concerns.lower()
        if 'トス' in user_concerns or 'toss' in concerns_lower:
            return "トスの安定性向上のため、毎日10回、同じ高さ・同じ位置にトスを上げる練習を行いましょう。"
        elif '威力' in user_concerns or 'パワー' in user_concerns or 'power' in concerns_lower:
            return "サーブの威力向上には、体幹の回転を意識し、下半身から上半身への運動連鎖を強化しましょう。"
        elif 'フォーム' in user_concerns or 'form' in concerns_lower:
            return "フォームの安定には、鏡の前でのスロー練習を週3回、各10分間行うことが効果的です。"
        elif 'コントロール' in user_concerns or 'control' in concerns_lower:
            return "コントロール向上のため、ターゲットを設置してのサーブ練習を1日20球から始めましょう。"
        else:
            return "まずは基本的なサーブフォームの確認から始め、一つずつ改善点を意識して練習しましょう。"

    def _call_chatgpt_api(self, prompt: str, language: str = 'ja') -> Optional[str]:
        try:
            if language == "ja":
                system_content = "あなたは30年以上の経験を持つATP/WTAツアーのプロテニスコーチです。下記「ユーザーの具体的な悩み」に必ず明確かつ具体的に答えてください。"
            elif language == "en":
                system_content = "You are a professional tennis coach with over 30 years of ATP/WTA tour experience. Always respond clearly and concretely to the user's specific concerns below."
            elif language == "es":
                system_content = "Eres un entrenador profesional de tenis con más de 30 años de experiencia en el circuito ATP/WTA. Responde siempre de forma clara y concreta a las inquietudes específicas del usuario a continuación."
            else:
                system_content = "You are a highly experienced tennis coach. Always respond clearly and concretely to the user's concerns."

            if self.client:
                logger.info("OpenAI v1.0+ APIを使用")
                response = self.client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                logger.info("OpenAI v0.x APIを使用")
                import openai
                response = openai.ChatCompletion.create(
                    model="gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"ChatGPT API呼び出しエラー: {e}")
            return None

    def _generate_fallback_advice(self) -> Dict:
        return {
            "basic_advice": "サーブフォームの基本を確認し、段階的に改善していきましょう。",
            "technical_points": [
                "正しいスタンスの確認",
                "トスの一貫性向上",
                "スムーズなスイング動作"
            ],
            "practice_suggestions": [
                "基本フォームの反復練習",
                "ターゲット練習",
                "スロー練習からの段階的向上"
            ],
            "enhanced": False,
            "error": "アドバイス生成中にエラーが発生しました"
        }