#!/usr/bin/env python3
"""Patch AstroPhysic quiz and study cards with a persistent wrong-answer review flow.
Run in the repository root: python add_wrong_answer_review.py
"""
from pathlib import Path

quiz_path = Path('index.html')
study_path = Path('study-cards/index.html')

def replace_once(text, before, after, label):
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, got {count}; files may have changed or already been patched')
    return text.replace(before, after, 1)

quiz = quiz_path.read_text(encoding='utf-8')
study = study_path.read_text(encoding='utf-8')
quiz = replace_once(quiz, 'function buildExam(container,items,opts){', '''// Both pages share the original 54-question order (quiz index + 1 = study-card id).
const MISTAKES_KEY="astro-w1-w3-mistakes-v1";
function saveQuizOutcome(questionIndex,isCorrect){
  try{
    const stored=JSON.parse(localStorage.getItem(MISTAKES_KEY)||"[]");
    const missed=new Set(Array.isArray(stored)?stored:[]);
    const id=questionIndex+1;
    if(isCorrect)missed.delete(id);else missed.add(id);
    localStorage.setItem(MISTAKES_KEY,JSON.stringify([...missed].sort((a,b)=>a-b)));
  }catch(error){console.warn("Could not save review progress",error);}
}
function buildExam(container,items,opts){''', 'quiz storage helper')
quiz = replace_once(quiz, '    c.card.classList.add(mine===right?"correct":(mine===null?"skipped":"wrong"));', '''    c.card.classList.add(mine===right?"correct":(mine===null?"skipped":"wrong"));
    // Skipped questions are not treated as demonstrated misconceptions.
    if(mine!==null)saveQuizOutcome(c.it.qi,mine===right);''', 'quiz incorrect tracking')
quiz = replace_once(quiz, '    results.innerHTML=`<p class="eyebrow" style="margin:0">Result</p>', '''    const missedCount=cards.filter((c,n)=>answers[n]!==null&&answers[n]!==c.it.order.indexOf(c.d.a)).length;
    results.innerHTML=`<p class="eyebrow" style="margin:0">Result</p>''', 'quiz score count')
quiz = replace_once(quiz, '<div class="bars">${rows}</div>`;', '<div class="bars">${rows}</div><a class="btn" style="display:inline-block;text-decoration:none;align-self:flex-start" href="/study-cards/?review=wrong">Review wrong answers (${missedCount} in this attempt) →</a>`;', 'quiz review link')

study = replace_once(study, '<option value="saved">★ Bookmarked</option>', '<option value="saved">★ Bookmarked</option><option value="wrong">✗ Wrong answers</option>', 'study select filter')
study = replace_once(study, '<div class="stat"><strong id="savedCount"', '<div class="stat"><strong id="wrongCount">0</strong><small>To review from quizzes</small></div><div class="stat"><strong id="savedCount"', 'study count badge')
study = replace_once(study, "const $=id=>document.getElementById(id);const storageKey=", "const $=id=>document.getElementById(id);const mistakesKey='astro-w1-w3-mistakes-v1';function getMissed(){try{const ids=JSON.parse(localStorage.getItem(mistakesKey)||'[]');return new Set(Array.isArray(ids)?ids.filter(id=>Number.isInteger(id)&&id>=1&&id<=DATA.length):[])}catch{return new Set()}}let missed=getMissed();const storageKey=", 'study storage helper')
study = replace_once(study, "(status==='saved'&&saved.has(d.id)))", "(status==='saved'&&saved.has(d.id))||(status==='wrong'&&missed.has(d.id)))", 'study wrong filter logic')
study = replace_once(study, "${done?'<span class=\"tag done\">STUDIED</span>':''}", "${done?'<span class=\"tag done\">STUDIED</span>':''}${missed.has(x.id)?'<span class=\"tag\" style=\"background:#562c39;color:#ffc0c0\">NEEDS REVIEW</span>':''}", 'study needs review tags')
study = replace_once(study, "$('savedCount').textContent=saved.size;", "$('savedCount').textContent=saved.size;$('wrongCount').textContent=missed.size;", 'study wrong count')
study = replace_once(study, "$('reset').addEventListener('click',()=>{if(confirm('Clear all studied and bookmarked cards?')){studied.clear();saved.clear();persist();render()}});renderTopics();render();", """$('reset').addEventListener('click',()=>{if(confirm('Clear studied, bookmarked, and wrong-answer progress?')){studied.clear();saved.clear();missed.clear();persist();try{localStorage.removeItem(mistakesKey)}catch{}render()}});
window.addEventListener('storage',e=>{if(e.key===mistakesKey){missed=getMissed();render()}});
if(new URLSearchParams(location.search).get('review')==='wrong'){
  $('status').value='wrong';week='all';topic='all';
}
renderTopics();render();""", 'study init and resets')

# Only write once every patch operation has validated.
quiz_path.write_text(quiz, encoding='utf-8')
study_path.write_text(study, encoding='utf-8')
print('Patched index.html and study-cards/index.html successfully.')
