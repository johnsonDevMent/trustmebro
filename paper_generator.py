"""
Paper Generator for TRUSTMEBRO
Generates parody research papers with fictional data
"""

import random
import hashlib
import json
import re
import os

# Try to import Groq SDK, but make it optional
try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False

# HTTP fallback for Groq API
def groq_api_call(api_key, messages, max_tokens=500, temperature=0.85):
    """Direct HTTP call to Groq API as fallback"""
    try:
        import urllib.request
        import urllib.error
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"[GROQ HTTP] ❌ API call failed: {e}")
        return None


class PaperGenerator:
    """Generate parody research papers"""
    
    # Fictional institutions - NAIJA
    INSTITUTIONS_NAIJA = [
        "University of Unverified Studies, Lagos",
        "Institute for Dubious Research, Abuja",
        "College of Questionable Sciences, Port Harcourt",
        "Academy of Anecdotal Evidence, Ibadan",
        "School of Confident Misunderstandings, Kano",
        "Department of Bro Science, Fictional State University",
        "Center for Hearsay Studies, Enugu",
        "Faculty of Trust Me Research, Benin City",
        "National Institute of Made-Up Statistics, Calabar",
        "Federal University of Unsourced Claims, Kaduna",
    ]
    
    # Fictional institutions - GLOBAL
    INSTITUTIONS_GLOBAL = [
        "University of Unverified Studies, Stockholm",
        "Institute for Dubious Research, Geneva",
        "College of Questionable Sciences, Vienna",
        "Academy of Anecdotal Evidence, Toronto",
        "School of Confident Misunderstandings, Melbourne",
        "Department of Bro Science, Fictional State University",
        "Center for Hearsay Studies, Edinburgh",
        "Faculty of Trust Me Research, Copenhagen",
        "International Institute of Made-Up Data, Zurich",
        "Global Center for Unsourced Research, Amsterdam",
    ]
    
    # Fictional first names
    FIRST_NAMES_NAIJA = [
        "Chukwuemeka", "Oluwaseun", "Adebayo", "Ngozi", "Chidinma",
        "Emeka", "Folake", "Tunde", "Amaka", "Obiora", "Yetunde",
        "Ikechukwu", "Funke", "Babatunde", "Chinwe"
    ]
    
    FIRST_NAMES_GLOBAL = [
        "Alexander", "Victoria", "Sebastian", "Eleanor", "Theodore",
        "Penelope", "Harrison", "Cordelia", "Benjamin", "Margaret",
        "Nathaniel", "Catherine", "Frederick", "Elizabeth", "William"
    ]
    
    # Fictional surnames
    SURNAMES_NAIJA = [
        "Okonkwo", "Adeyemi", "Nwachukwu", "Ibrahim", "Okafor",
        "Balogun", "Eze", "Abubakar", "Okoro", "Adeleke",
        "Obi", "Mohammed", "Chukwu", "Afolabi", "Nnamdi"
    ]
    
    SURNAMES_GLOBAL = [
        "Worthington", "Pemberton", "Ashford", "Blackwood", "Sterling",
        "Whitmore", "Harrington", "Caldwell", "Montgomery", "Fitzgerald",
        "Chamberlain", "Wellington", "Kensington", "Thornbury", "Fairfax"
    ]
    
    # Fictional journals
    JOURNALS = [
        "Journal of Improbable Findings",
        "Quarterly Review of Unsubstantiated Claims",
        "International Journal of Anecdotal Science",
        "Proceedings of the Fictional Research Society",
        "Archives of Dubious Studies",
        "Bulletin of Made-Up Statistics",
        "Annals of Unverified Research",
        "Journal of Confident Assertions",
    ]
    
    # Fictional conferences
    CONFERENCES = [
        "International Conference on Unverified Claims (ICUC)",
        "World Symposium on Made-Up Science (WSMS)",
        "Global Forum on Dubious Research (GFDR)",
        "Annual Meeting of Fictional Researchers (AMFR)",
        "Conference on Anecdotal Evidence (CAE)",
    ]
    
    def __init__(self, groq_key=None):
        self.groq_key = groq_key
        self.groq_client = None
        self.use_http_fallback = False
        
        if groq_key:
            if GROQ_SDK_AVAILABLE:
                try:
                    # Set API key via environment variable (recommended by Groq)
                    os.environ['GROQ_API_KEY'] = groq_key
                    self.groq_client = Groq()
                    print(f"[GROQ] ✅ Groq SDK initialized (key: {groq_key[:8]}...)")
                except Exception as e:
                    print(f"[GROQ] ⚠️ SDK init failed: {e}")
                    print(f"[GROQ] ℹ️ Will use HTTP fallback for API calls")
                    self.use_http_fallback = True
            else:
                print("[GROQ] ℹ️ Groq SDK not installed, using HTTP fallback")
                self.use_http_fallback = True
        else:
            print("[GROQ] ℹ️ No Groq key - using templates only")
    
    def _call_groq(self, messages, max_tokens=500, temperature=0.85):
        """Call Groq API using SDK or HTTP fallback"""
        # Try SDK first
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[GROQ] ⚠️ SDK call failed: {e}")
                print(f"[GROQ] ℹ️ Trying HTTP fallback...")
        
        # HTTP fallback
        if self.groq_key:
            result = groq_api_call(self.groq_key, messages, max_tokens, temperature)
            if result:
                return result.strip()
        
        return None
    
    def _seed_random(self, claim, lock_seed):
        """Set random seed for deterministic output"""
        if lock_seed:
            seed = int(hashlib.md5(claim.encode()).hexdigest()[:8], 16)
            random.seed(seed)
        else:
            random.seed()
    
    def _generate_paper_id(self):
        """Generate unique paper ID"""
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        suffix = ''.join(random.choice(chars) for _ in range(5))
        return f'TMB-{suffix}'
    
    def _generate_authors(self, voice, count=3):
        """Generate fictional author names"""
        if voice == 'naija':
            first_names = self.FIRST_NAMES_NAIJA
            surnames = self.SURNAMES_NAIJA
        else:
            first_names = self.FIRST_NAMES_GLOBAL
            surnames = self.SURNAMES_GLOBAL
        
        authors = []
        used_surnames = set()
        for _ in range(count):
            surname = random.choice([s for s in surnames if s not in used_surnames] or surnames)
            used_surnames.add(surname)
            first = random.choice(first_names)
            middle = chr(random.randint(65, 90))
            authors.append(f"{surname}, {first[0]}. {middle}.")
        
        return authors
    
    def _generate_affiliations(self, voice, count=2):
        """Generate fictional affiliations"""
        institutions = self.INSTITUTIONS_NAIJA if voice == 'naija' else self.INSTITUTIONS_GLOBAL
        return random.sample(institutions, min(count, len(institutions)))
    
    def _generate_title(self, claim, template):
        """Generate paper title"""
        prefixes = {
            'journal': [
                "A Rigorous Investigation into",
                "Empirical Evidence Supporting",
                "A Meta-Analysis of",
                "Correlational Study of",
                "Cross-Sectional Analysis of",
                "The Definitive Study on",
                "Quantitative Assessment of",
            ],
            'conference': [
                "Towards Understanding",
                "Novel Insights into",
                "Preliminary Findings on",
                "An Exploratory Study of",
                "Investigating the Relationship Between",
                "New Evidence for",
            ],
            'thesis': [
                "An Investigation into",
                "A Comprehensive Study of",
                "Exploring the Phenomenon of",
                "Understanding the Dynamics of",
                "A Critical Analysis of",
            ]
        }
        
        prefix = random.choice(prefixes.get(template, prefixes['journal']))
        clean_claim = self._normalize_percent(claim.strip().rstrip('.!?'))
        return f"{prefix} {clean_claim}"
    
    def _normalize_percent(self, text):
        """Convert 'percent' and 'per cent' to '%' symbol"""
        import re
        # Match number followed by percent/per cent
        text = re.sub(r'(\d+)\s*percent', r'\1%', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*per\s*cent', r'\1%', text, flags=re.IGNORECASE)
        # Also handle "X percent" without number directly before
        text = re.sub(r'\bpercent\b', '%', text, flags=re.IGNORECASE)
        text = re.sub(r'\bper\s*cent\b', '%', text, flags=re.IGNORECASE)
        return text
    
    def _generate_abstract_template(self, claim, voice, tone):
        """Generate abstract using templates (no Groq)"""
        sample_size = random.randint(500, 5000)
        percentage = random.randint(45, 85)
        p_value = round(random.uniform(0.001, 0.04), 3)
        ci_low = percentage - random.randint(3, 8)
        ci_high = percentage + random.randint(3, 8)
        
        # Normalize percent in claim
        normalized_claim = self._normalize_percent(claim.lower())
        
        if voice == 'naija':
            intros = [
                f"This study investigates the widely circulated claim that {normalized_claim}.",
                f"Following numerous reports from trusted sources (specifically, \"my brother told me\"), we examine whether {normalized_claim}.",
                f"In response to growing discourse on social media platforms, this research explores the assertion that {normalized_claim}.",
            ]
        else:
            intros = [
                f"This research investigates the hypothesis that {normalized_claim}.",
                f"Building upon anecdotal evidence from various sources, we examine the claim that {normalized_claim}.",
                f"The present study aims to empirically evaluate the proposition that {normalized_claim}.",
            ]
        
        intro = random.choice(intros)
        
        if tone == 'deadpan':
            method = f"A simulated observational study was conducted with N={sample_size} fictional participants across multiple imaginary locations. Data were collected using entirely fabricated questionnaires and analyzed using non-existent statistical software."
            result = f"Results indicate a {percentage}% correlation with the stated hypothesis (95% CI: [{ci_low}%, {ci_high}%], p < {p_value}, simulated). Effect size was deemed \"definitely significant\" by our fictional standards."
        else:
            method = f"We surveyed {sample_size} entirely made-up participants who definitely exist and weren't just imagined for this paper. Our methodology was peer-reviewed by our imagination."
            result = f"Amazingly, {percentage}% of our fictional respondents agreed with the hypothesis (p < {p_value}, which we promise is real). The remaining {100-percentage}% were clearly not paying attention."
        
        limitation = "This study is entirely fictional and should not be cited in any serious academic work. All data presented is simulated for parody purposes only."
        
        return f"{intro} {method} {result} {limitation}"
    
    def _analyze_topic(self, claim):
        """Analyze claim to determine topic domain and generate relevant jargon"""
        claim_lower = claim.lower()
        
        # Science/Chemistry keywords
        if any(w in claim_lower for w in ['glucose', 'chemical', 'molecule', 'atom', 'reaction', 'acid', 'base', 'compound', 'element', 'oxygen', 'carbon', 'protein', 'enzyme', 'cell', 'dna', 'rna']):
            return {
                'domain': 'biochemistry',
                'jargon': ['molecular concentration', 'enzymatic activity', 'substrate binding', 'metabolic pathway', 'cellular uptake', 'bioavailability'],
                'formulas': ['C₆H₁₂O₆ (glucose)', 'ATP → ADP + Pi', 'ΔG = -RT ln K', 'pH = -log[H⁺]'],
                'units': ['mol/L', 'μM', 'kDa', 'nm'],
                'methods': ['spectrophotometry', 'chromatography', 'mass spectrometry', 'Western blot analysis']
            }
        
        # Physics keywords
        elif any(w in claim_lower for w in ['energy', 'force', 'gravity', 'speed', 'light', 'quantum', 'wave', 'particle', 'electric', 'magnetic', 'momentum']):
            return {
                'domain': 'physics',
                'jargon': ['wave function', 'quantum superposition', 'electromagnetic field', 'kinetic energy', 'potential energy'],
                'formulas': ['E = mc²', 'F = ma', 'ΔE = hν', 'p = mv', 'λ = h/p'],
                'units': ['J', 'N', 'eV', 'm/s²', 'Hz'],
                'methods': ['interferometry', 'particle acceleration', 'spectral analysis', 'calorimetry']
            }
        
        # Food/Nutrition keywords
        elif any(w in claim_lower for w in ['food', 'eat', 'rice', 'diet', 'nutrition', 'calorie', 'meal', 'cooking', 'taste', 'spoon', 'fork', 'stew', 'vitamin']):
            return {
                'domain': 'nutrition',
                'jargon': ['caloric intake', 'macronutrient balance', 'glycemic index', 'satiety response', 'dietary compliance'],
                'formulas': ['BMI = kg/m²', 'TEE = BMR × PAL', 'DRI = EAR + 2SD'],
                'units': ['kcal', 'g/serving', 'mg/dL', 'IU'],
                'methods': ['food frequency questionnaire', 'dietary recall', 'metabolic assessment', 'anthropometric measurement']
            }
        
        # Psychology/Social keywords
        elif any(w in claim_lower for w in ['people', 'person', 'think', 'feel', 'behavior', 'social', 'mental', 'happy', 'sad', 'stress', 'intelligence', 'personality']):
            return {
                'domain': 'psychology',
                'jargon': ['cognitive load', 'behavioral pattern', 'psychometric assessment', 'self-efficacy', 'emotional regulation'],
                'formulas': ['d = (M₁ - M₂) / σ', 'r² = explained variance', 'α > 0.7 (reliability)'],
                'units': ['SD', 'percentile', 'z-score', 'Likert scale'],
                'methods': ['self-report inventory', 'behavioral observation', 'neuroimaging', 'longitudinal analysis']
            }
        
        # Technology keywords
        elif any(w in claim_lower for w in ['computer', 'phone', 'internet', 'app', 'software', 'code', 'data', 'ai', 'machine', 'digital', 'algorithm']):
            return {
                'domain': 'technology',
                'jargon': ['computational efficiency', 'algorithmic complexity', 'data throughput', 'system latency', 'API integration'],
                'formulas': ['O(n log n)', 'T(n) = 2T(n/2) + n', 'bandwidth = bits/second'],
                'units': ['ms', 'MB/s', 'FLOPS', 'requests/sec'],
                'methods': ['A/B testing', 'benchmark analysis', 'user analytics', 'load testing']
            }
        
        # Economics/Money keywords
        elif any(w in claim_lower for w in ['money', 'rich', 'poor', 'economy', 'price', 'cost', 'income', 'wealth', 'salary', 'profit', 'market']):
            return {
                'domain': 'economics',
                'jargon': ['marginal utility', 'price elasticity', 'market equilibrium', 'opportunity cost', 'comparative advantage'],
                'formulas': ['ROI = (gain - cost) / cost', 'PV = FV / (1+r)ⁿ', 'GDP = C + I + G + NX'],
                'units': ['$', '% APR', 'basis points', 'PPP'],
                'methods': ['econometric modeling', 'regression analysis', 'market survey', 'panel data analysis']
            }
        
        # Default generic
        else:
            return {
                'domain': 'general',
                'jargon': ['statistical significance', 'effect size', 'confidence interval', 'correlation coefficient'],
                'formulas': ['p < 0.05', 'r = 0.7', 'CI = 95%'],
                'units': ['%', 'SD', 'n'],
                'methods': ['survey methodology', 'observational study', 'cross-sectional analysis']
            }
    
    def _generate_title_groq(self, claim, template, voice='global', tone='deadpan'):
        """Generate creative academic title using Groq"""
        if not self.groq_client and not self.use_http_fallback:
            print("[GROQ] ❌ No Groq available for title - using template")
            return self._generate_title(claim, template)
        
        print(f"[GROQ] 🚀 Calling Groq API for title...")
        
        # Voice-specific title style
        if voice == 'naija':
            voice_hint = "Can include subtle Nigerian cultural references or wordplay if relevant"
        else:
            voice_hint = "Use standard international academic title conventions"
        
        # Tone-specific title style
        if tone == 'deadpan':
            tone_hint = "Make it sound completely serious and legitimate"
        else:
            tone_hint = "Can include subtle wit or clever wordplay"
        
        prompt = f"""Generate a creative, academic-sounding research paper title for this ridiculous claim: "{claim}"

STYLE:
- {voice_hint}
- {tone_hint}

REQUIREMENTS:
- Sound like a real {template} article title
- Include a colon with a subtitle if appropriate
- Use % symbol instead of "percent"
- Examples of good parody titles:
  - "Correlation Without Causation: A Meta-Analysis of Things That Sound Related"
  - "The Placebo Effect of Confidence: Why Saying Things Loudly Makes Them True"
  - "Spoons and Society: Cutlery as a Predictor of Socioeconomic Status"

Generate ONLY the title, nothing else. No quotes around it."""

        import time
        start = time.time()
        
        result = self._call_groq(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.9
        )
        
        if result:
            elapsed = time.time() - start
            title = result.strip('"\'')
            title = self._normalize_percent(title)
            print(f"[GROQ] ✅ Title received in {elapsed:.2f}s: {title[:60]}...")
            return title
        else:
            print(f"[GROQ] ❌ Title generation failed - using template")
            return self._generate_title(claim, template)
    
    def _generate_abstract_groq(self, claim, voice, tone):
        """Generate abstract using Groq API with topic-aware content"""
        if not self.groq_client and not self.use_http_fallback:
            print("[GROQ] ❌ No Groq available - using template")
            return self._generate_abstract_template(claim, voice, tone)
        
        print(f"[GROQ] 🚀 Calling Groq API for abstract...")
        print(f"[GROQ]    Claim: {claim[:50]}...")
        
        # Analyze topic for domain-specific content
        topic = self._analyze_topic(claim)
        print(f"[GROQ]    Detected domain: {topic['domain']}")
        print(f"[GROQ]    Voice: {voice} | Tone: {tone}")
        
        # Voice-specific instructions (NAIJA vs GLOBAL)
        if voice == 'naija':
            voice_instruction = """NIGERIAN ENGLISH VOICE:
- Use Nigerian expressions like "sha", "abi", "na so", "wahala", "gist"  
- Reference Nigerian contexts (Lagos traffic, NEPA/light, jollof rice debates, etc.)
- Use Nigerian academic humor ("as per my last email" → "as per my last WhatsApp voice note")
- Include relatable Nigerian scenarios in examples
- May reference fictional Nigerian institutions
- Casual but academic tone typical of Nigerian academia"""
        else:
            voice_instruction = """INTERNATIONAL ACADEMIC VOICE:
- Use formal British/American academic English
- Reference global/Western contexts
- Maintain traditional academic formality
- Use standard academic phrases and conventions
- Reference fictional international institutions"""
        
        # Tone-specific instructions (DEADPAN vs COMEDIC)
        if tone == 'deadpan':
            tone_instruction = """DEADPAN SERIOUS TONE:
- Write as if this is completely legitimate research
- NO jokes, NO winks to the audience
- Maintain absolute academic seriousness throughout
- Let the absurdity of the claim create the humor
- Use overly formal language for mundane observations
- Cite fictional studies with complete seriousness
- The humor comes from treating nonsense as serious science"""
        else:
            tone_instruction = """COMEDIC/WITTY TONE:
- Include subtle academic humor and wit
- Use dry observations and ironic commentary
- Self-aware about the absurdity of the research
- Include clever wordplay related to the topic
- Break the fourth wall slightly ("as the researchers definitely didn't make up")
- Use humorous asides in parentheses
- Make fun of academic conventions while using them"""
        
        # Build domain-specific instructions
        domain_instructions = f"""
DOMAIN: {topic['domain'].upper()}
Include domain-specific elements:
- Jargon: {', '.join(topic['jargon'][:3])}
- Formulas/notation: {', '.join(topic['formulas'][:2])}
- Units: {', '.join(topic['units'][:2])}
- Methods: {', '.join(topic['methods'][:2])}
"""
        
        prompt = f"""Generate a parody academic abstract for this ridiculous claim: "{claim}"

{voice_instruction}

{tone_instruction}

{domain_instructions}

REQUIREMENTS:
- 150-200 words
- Include fake sample size (N=500-5000)
- Include percentage results using % symbol (45-85%)
- Include fake p-value (p < 0.001-0.04)
- Include at least ONE relevant formula or technical notation from the domain
- Reference "simulated" or "fictional" methodology
- End with disclaimer that this is fictional/parody
- Do NOT use real institution names or real people

Generate ONLY the abstract text, nothing else."""

        import time
        start = time.time()
        
        result = self._call_groq(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.85
        )
        
        if result:
            elapsed = time.time() - start
            abstract = result
            
            print(f"[GROQ] ✅ Response received in {elapsed:.2f}s")
            print(f"[GROQ]    Response length: {len(abstract)} chars")
            print(f"[GROQ]    Preview: {abstract[:100]}...")
            
            # Ensure it has disclaimer
            if "fictional" not in abstract.lower() and "parody" not in abstract.lower():
                abstract += " This study is entirely fictional and should not be cited in any academic work."
            
            # Replace "percent" with "%"
            abstract = self._normalize_percent(abstract)
            
            return abstract
        else:
            print(f"[GROQ] ❌ Abstract generation failed - using template")
            return self._generate_abstract_template(claim, voice, tone)
    
    def _generate_introduction(self, claim, voice, tone):
        """Generate introduction section"""
        if tone == 'deadpan':
            template = f"""The phenomenon described as "{claim}" has garnered significant attention in recent discourse, particularly in informal settings where rigorous scientific methodology is often secondary to persuasive anecdote.

Previous research in related areas has been notably absent, creating what we term a "knowledge vacuum" that this study aims to address through entirely fabricated means. The theoretical framework underlying this investigation draws from the established field of "things people say at parties" (Fictional et al., 2023).

The present study contributes to the literature by providing the first completely made-up empirical evidence for this claim. Our research questions are as follows: (1) Is the claim true? (2) Can we make it look true with fake data? (3) Will anyone actually read past the abstract?"""
        else:
            template = f"""Let's be honest: someone at a party said "{claim}" and it sounded so confident that we decided to "prove" it with science.

The academic literature on this topic is, unsurprisingly, non-existent. We looked. We really did. For about five minutes. This conspicuous absence of research clearly indicates either a massive oversight by the scientific community or, more likely, that nobody thought this needed formal study until now.

This groundbreaking investigation seeks to answer the age-old questions: Is this claim true? More importantly, can we make a convincing-looking paper about it? Spoiler alert: the answer to both is "kind of, but not really.\""""
        
        return template
    
    def _generate_methods(self, claim, voice, tone, template_type):
        """Generate methods section"""
        sample_size = random.randint(500, 5000)
        locations = random.randint(3, 12)
        duration = random.choice(["6 months", "1 year", "2 years", "an undisclosed period"])
        
        method_section = f"""**Simulated Study Design**

This study employed a fictional mixed-methods approach combining imaginary quantitative surveys with entirely made-up qualitative interviews.

**Participants**
A total of N={sample_size} fictional participants were recruited from {locations} imaginary locations. Inclusion criteria included: being completely made up, existing only in this paper, and having no verifiable identity whatsoever.

**Data Collection**
Data were collected over {duration} using instruments that do not actually exist. The primary measure was the Fictional Assessment Scale (FAS), which we just invented for this study.

**Statistical Analysis**
All analyses were performed using StatsFaker Pro™ (Imaginary Software Inc., 2024). We employed regression analysis, ANOVA, and several other statistical tests that sound impressive but were applied to completely fabricated data.

**Ethical Considerations**
This study received approval from the Fictional Ethics Board of Made-Up Research (FEBMUR), Certificate No. FAKE-{random.randint(1000, 9999)}. No real humans were involved because no real research was conducted."""

        if template_type == 'thesis':
            method_section += """

**Note from the Faculty of Parody Studies**
This methodology section is presented in standard academic format for satirical purposes. The Faculty of Parody Studies approves this fictional approach to non-research."""
        
        return method_section
    
    def _generate_results(self, claim, voice, tone):
        """Generate results section"""
        main_pct = random.randint(45, 85)
        secondary_pct = random.randint(30, 60)
        p_value = round(random.uniform(0.001, 0.04), 3)
        effect_size = round(random.uniform(0.3, 0.8), 2)
        
        return f"""**Fabricated Findings**

The primary analysis revealed strong fictional support for the hypothesis that {claim.lower()}. Specifically, {main_pct}% of our imaginary participants demonstrated the predicted effect (p < {p_value}, Cohen's d = {effect_size}).

Secondary analyses, which we conducted after seeing the primary results, also supported our predetermined conclusions. A total of {secondary_pct}% of participants in the fictional control group showed no effect whatsoever, which we interpret as further evidence for our hypothesis.

Subgroup analyses revealed that the effect was strongest among participants who were most conveniently made up to support our claims. Demographic variations were observed but will not be reported because we didn't actually collect demographic data.

All results should be interpreted with the understanding that they are entirely fictional and represent no actual empirical findings whatsoever."""
    
    def _generate_discussion(self, claim, voice, tone):
        """Generate discussion section"""
        return f"""The present study provides compelling fictional evidence that {claim.lower()}. These fabricated findings have important imaginary implications for both theory and practice.

Our results are consistent with previous work that doesn't exist, suggesting a robust pattern of made-up evidence across multiple non-studies. The theoretical contributions of this work include demonstrating that with sufficient creativity, one can generate academic-looking content about virtually any claim.

**Practical Implications**
If these findings were real (they are not), they would suggest that people should probably reconsider their assumptions about this topic. However, since everything here is fictional, the primary practical implication is entertainment value.

**Strengths and Limitations**
The main strength of this study is its creative use of entirely fabricated data to support a predetermined conclusion. The main limitation is that none of it is real. Other limitations include: we made everything up, the sample doesn't exist, and the statistical analyses were performed on imaginary numbers.

**Future Directions**
Future research should continue to not be done, as this topic requires no actual investigation. Should anyone feel compelled to study this for real, they should probably find a more productive use of their time."""
    
    def _generate_limitations(self, voice, tone, template_type):
        """Generate limitations section"""
        base = """**Study Limitations & Parody Disclaimer**

This study has several methodological limitations that warrant acknowledgment:

1. **All data is fictional.** No actual research was conducted for this paper.
2. **Participants do not exist.** Every participant mentioned is entirely imaginary.
3. **Statistical analyses are meaningless.** The numbers were generated to look impressive, not to reflect reality.
4. **Conclusions are predetermined.** We decided what we wanted to "find" before "collecting" data.
5. **This is parody.** This document is intended for entertainment purposes only.

**DO NOT CITE THIS PAPER IN ANY SERIOUS ACADEMIC WORK.**

This research was generated by TRUSTMEBRO, a parody research paper generator. All authors, affiliations, journals, and findings are completely fictional."""

        if voice == 'naija' and tone == 'comedic':
            base += "\n\nNa joke we dey joke, no go cite am for your thesis abeg. Your supervisor go find you."
        
        if template_type == 'thesis':
            base += """

**Submitted to the Faculty of Parody Studies**
This thesis was submitted in partial fulfillment of the requirements for the imaginary degree of Master of Made-Up Science (M.MUS) at the Fictional University. Academic formatting used for parody purposes only."""
        
        return base
    
    def _generate_references(self, voice, count=4):
        """Generate fictional references"""
        refs = []
        years = list(range(2019, 2025))
        
        for i in range(count):
            author = self._generate_authors(voice, random.randint(1, 3))
            year = random.choice(years)
            journal = random.choice(self.JOURNALS)
            vol = random.randint(1, 50)
            issue = random.randint(1, 4)
            pages_start = random.randint(1, 100)
            pages_end = pages_start + random.randint(10, 30)
            
            titles = [
                "On the Nature of Unverified Claims",
                "A Framework for Dubious Research Methodology",
                "The Role of 'Trust Me, Bro' in Modern Discourse",
                "Statistical Methods for Imaginary Data",
                "Fabricating Evidence: A Practical Guide",
                "Why Nobody Reads Past the Abstract",
                "Confirmation Bias: A How-To Manual",
                "P-Hacking for Beginners",
            ]
            
            title = random.choice(titles)
            author_str = "; ".join(author)
            
            refs.append(f"{author_str} ({year}). \"{title}\" [FICTIONAL]. {journal}, {vol}({issue}), {pages_start}-{pages_end}.")
        
        return refs
    
    def _generate_chart_data(self, claim, chart_count, topic=None):
        """Generate chart data specifications with topic awareness"""
        if topic is None:
            topic = self._analyze_topic(claim)
        
        charts = []
        chart_types = ['bar', 'pie', 'line']
        
        # Domain-specific Y-axis labels
        y_labels = {
            'biochemistry': ['Concentration (μM)', 'Enzyme Activity (%)', 'Binding Affinity'],
            'physics': ['Energy (J)', 'Force (N)', 'Frequency (Hz)'],
            'nutrition': ['Caloric Intake (kcal)', 'Nutrient Level (%)', 'Satisfaction Score'],
            'psychology': ['Response Score', 'Cognitive Load (%)', 'Behavioral Index'],
            'technology': ['Processing Time (ms)', 'Efficiency (%)', 'User Engagement'],
            'economics': ['Value ($)', 'ROI (%)', 'Market Share (%)'],
            'general': ['Agreement Level (%)', 'Effect Size', 'Response Rate (%)']
        }
        
        y_label_options = y_labels.get(topic['domain'], y_labels['general'])
        
        for i in range(chart_count):
            chart_type = chart_types[i % len(chart_types)]
            
            if chart_type == 'bar':
                labels = ["Control Group", "Test Group A", "Test Group B", "Believers", "Skeptics"][:random.randint(3, 5)]
                data = [random.randint(20, 80) for _ in labels]
                charts.append({
                    'type': 'bar',
                    'title': f'Figure {i+1}: Correlation Analysis',
                    'x_label': 'Participant Groups',
                    'y_label': random.choice(y_label_options),
                    'labels': labels,
                    'data': data,
                    'caption': f'Figure {i+1}. Simulated data for parody purposes. Error bars represent fictional confidence intervals.'
                })
            elif chart_type == 'pie':
                labels = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
                data = [random.randint(10, 40) for _ in labels]
                # Normalize to 100
                total = sum(data)
                data = [round(d/total*100, 1) for d in data]
                charts.append({
                    'type': 'pie',
                    'title': f'Figure {i+1}: Response Distribution',
                    'labels': labels,
                    'data': data,
                    'caption': f'Figure {i+1}. Distribution of fictional responses. All data is simulated.'
                })
            else:  # line
                labels = [f'Week {w}' for w in range(1, 9)]
                data = [random.randint(30, 50) + (i * random.randint(3, 7)) for i, _ in enumerate(labels)]
                charts.append({
                    'type': 'line',
                    'title': f'Figure {i+1}: Trend Over Time',
                    'x_label': 'Time Period',
                    'y_label': random.choice(y_label_options),
                    'labels': labels,
                    'data': data,
                    'caption': f'Figure {i+1}. Temporal trend in fabricated data. Pattern is entirely coincidental.'
                })
        
        return charts
    
    def generate(self, claim, template, length, voice, tone, chart_count, lock_seed):
        """Generate complete paper"""
        print(f"\n{'='*60}")
        print(f"[GENERATE] Starting paper generation")
        groq_available = self.groq_client is not None or self.use_http_fallback
        print(f"[GENERATE]   Claim: {claim[:50]}...")
        print(f"[GENERATE]   Length: {length} | Voice: {voice} | Tone: {tone}")
        print(f"[GENERATE]   Groq available: {groq_available}")
        print(f"[GENERATE]   Will use Groq: {groq_available and length in ['short', 'full']}")
        print(f"{'='*60}")
        
        self._seed_random(claim, lock_seed)
        
        paper_id = self._generate_paper_id()
        
        # Generate core elements
        # Use Groq for title if available and not abstract-only
        if groq_available and length in ['short', 'full']:
            title = self._generate_title_groq(claim, template, voice, tone)
        else:
            print("[GENERATE] Using template for title")
            title = self._generate_title(claim, template)
        
        authors = self._generate_authors(voice)
        affiliations = self._generate_affiliations(voice)
        
        # Generate abstract
        if groq_available and length in ['short', 'full']:
            abstract = self._generate_abstract_groq(claim, voice, tone)
        else:
            print("[GENERATE] Using template for abstract")
            abstract = self._generate_abstract_template(claim, voice, tone)
        
        # Generate limitations (always needed)
        limitations = self._generate_limitations(voice, tone, template)
        
        # Generate references
        ref_count = 4 if length == 'abstract' else (6 if length == 'short' else 8)
        references = self._generate_references(voice, ref_count)
        
        # Generate charts with topic awareness
        topic = self._analyze_topic(claim)
        charts = self._generate_chart_data(claim, chart_count, topic)
        
        paper_data = {
            'id': paper_id,
            'title': title,
            'authors': authors,
            'affiliations': affiliations,
            'abstract': abstract,
            'limitations': limitations,
            'references': references,
            'charts': charts,
        }
        
        # Add full sections for short/full papers
        if length in ['short', 'full']:
            paper_data['introduction'] = self._generate_introduction(claim, voice, tone)
            paper_data['methods'] = self._generate_methods(claim, voice, tone, template)
            paper_data['results'] = self._generate_results(claim, voice, tone)
            paper_data['discussion'] = self._generate_discussion(claim, voice, tone)
        
        print(f"[GENERATE] ✅ Paper generated: {paper_id}")
        return paper_data
