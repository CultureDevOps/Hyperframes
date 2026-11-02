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
        self.assertEqual(len(self.data['scenes']),8)
        for scene in self.data['scenes']:
            self.assertEqual(len(scene['cards']),3)
            self.assertGreaterEqual(len(scene['lines']),6)
            self.assertLess(max(len(k) for k in scene['cards']),32)
        self.assertEqual(len(set(s['id'] for s in self.data['scenes'])),8)
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
    def test_non_publishing_and_render_contract(self):
        for term in ('ffprobe','1280','720','30','libx264','aac','subtitles','espeak','mix.wav','picture-only.mp4'):
            self.assertIn(term,self.py)
        for forbidden in ('upload-artifact','github release','curl ','https://','requests.post'):
            self.assertNotIn(forbidden,self.py)
        self.assertIn('300<=duration<=420',self.py)
if __name__=='__main__':unittest.main()