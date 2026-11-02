"""Structural and editorial constraints for OPS-010 explanatory film."""
import json, pathlib, re, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
COMP=ROOT/'compositions/culturedevops/chatgpt-gitlab'
class ExplainerTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((COMP/'narration.json').read_text(encoding='utf8'))
        self.html=(COMP/'index.html').read_text(encoding='utf8')
        self.py=(ROOT/'scripts/render_chatgpt_gitlab.py').read_text(encoding='utf8')
    def test_structure(self):
        self.assertEqual(self.data['schema'],1)
        self.assertEqual(self.data['language'],'fr')
        self.assertEqual(len(self.data['scenes']),9)
        for scene in self.data['scenes']:
            self.assertEqual(len(scene['cards']),3)
            self.assertGreaterEqual(len(scene['lines']),5)
            self.assertLess(max(len(k) for k in scene['cards']),32)
        self.assertEqual(len(set(s['id'] for s in self.data['scenes'])),9)
    def test_hyperframes_720p_metadata(self):
        for attr in ('data-no-timeline','data-width="1280"','data-height="720"','data-fps="30"','data-composition-id='):
            self.assertIn(attr,self.html)
        self.assertIn('window.renderFrame',self.html)
        self.assertIn("textContent",self.html)
        self.assertNotIn('innerHTML',self.html)
    def test_fr_story_no_private_values_no_unsupported_savings(self):
        text=' '.join(s['title']+' '+' '.join(s['lines']) for s in self.data['scenes'])
        for fragment in ('Claude Code','ChatGPT','GitLab','checkpoint','Git'):
            self.assertIn(fragment,text)
        self.assertNotRegex(text, r'(?i)(?:\d{1,3}\s*%\s*d[’\']?économ|\d+\s*euros\s*économisés)')
        for path in (self.data['source'],self.html,text):
            self.assertNotIn('chatgpt.com/c/',path)
            self.assertNotIn('Bokashix/infrastructure-knowledge',path)
            self.assertNotIn('glpat-',path)
    def test_starter_and_stale_ci_synthetic_evidence(self):
        starter=next(s for s in self.data['scenes'] if s['id']=='starter')
        replay=next(s for s in self.data['scenes'] if s['id']=='reprise')
        self.assertEqual(len(starter['starter_steps']),3)
        self.assertEqual(len(replay['evidence_steps']),3)
        self.assertIn('bootstrap.py --destination ../labo-ops',starter['starter_steps'][0]['command'])
        self.assertIn('unittest discover',starter['starter_steps'][2]['command'])
        self.assertIn('CI #1002 : ÉCHEC',replay['evidence_steps'][1]['command'])
        self.assertIn('CI #1003 : SUCCÈS',replay['evidence_steps'][2]['command'])
        self.assertIn('demo-panel',self.html)
        self.assertIn('textContent=item.command',self.html)
        self.assertIn('Kit en revue',starter['footer'])
        sample=json.dumps(self.data,ensure_ascii=False)
        for forbidden in ('https://gitlab.com/Bokashix','chatgpt.com/c/','glpat-','sk-proj-'):
            self.assertNotIn(forbidden,sample)
    def test_narration_duration_editorial_budget(self):
        words=sum(len(' '.join(s['lines']).split()) for s in self.data['scenes'])
        self.assertGreaterEqual(words,730)
        self.assertLessEqual(words,1000)
    def test_non_publishing_and_render_contract(self):
        for term in ('ffprobe','1280','720','30','libx264','aac','subtitles','load_voice','mix.wav','picture-only.mp4'):
            self.assertIn(term,self.py)
        for forbidden in ('upload-artifact','github release','curl ','https://','requests.post'):
            self.assertNotIn(forbidden,self.py)
        self.assertIn('240<=duration<=600',self.py)
if __name__=='__main__':unittest.main()