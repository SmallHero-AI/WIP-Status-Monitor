import './style.css'

// Default food list
const DEFAULT_FOODS = [
  { name: '拉麵', emoji: '🍜' },
  { name: '壽司', emoji: '🍣' },
  { name: '披薩', emoji: '🍕' },
  { name: '漢堡', emoji: '🍔' },
  { name: '義大利麵', emoji: '🍝' },
  { name: '滷肉飯', emoji: '🍚' },
  { name: '牛肉麵', emoji: '🍜' },
  { name: '火鍋', emoji: '🍲' },
  { name: '牛排', emoji: '🥩' },
  { name: '便當', emoji: '🍱' },
  { name: '水餃', emoji: '🥟' },
  { name: '咖哩飯', emoji: '🍛' },
  { name: '燒肉', emoji: '🔥' },
  { name: '早午餐', emoji: '🍳' },
  { name: '沙拉', emoji: '🥗' }
];

const EMOJIS = ['🍔', '🍕', '🌮', '🍜', '🍱', '🥘', '🍲', '🍳', '🥗', '🍗', '🥩', '🥟', '🥪'];

// State
let foods = JSON.parse(localStorage.getItem('food-list')) || DEFAULT_FOODS;

// DOM Elements
const resultCard = document.getElementById('result-card');
const resultText = document.getElementById('result-text');
const resultEmoji = document.getElementById('result-emoji');
const decideBtn = document.getElementById('decide-btn');
const foodListEl = document.getElementById('food-list');
const foodInput = document.getElementById('food-input');
const addBtn = document.getElementById('add-btn');
const addToggle = document.getElementById('add-toggle');
const addForm = document.getElementById('add-form');
const toast = document.getElementById('toast');

// Initialize
function init() {
  renderFoodList();
}

function renderFoodList() {
  foodListEl.innerHTML = '';
  foods.forEach((food, index) => {
    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.innerHTML = `
      <span>${food.emoji} ${food.name}</span>
      <span class="delete" data-index="${index}">&times;</span>
    `;
    foodListEl.appendChild(tag);
  });

  // Add delete listeners
  document.querySelectorAll('.delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const index = e.target.dataset.index;
      removeFood(index);
    });
  });
}

function removeFood(index) {
  if (foods.length <= 2) {
    showToast('至少要保留兩個選項喔！');
    return;
  }
  foods.splice(index, 1);
  saveAndRender();
}

function addFood() {
  const name = foodInput.value.trim();
  if (!name) return;
  
  if (foods.some(f => f.name === name)) {
    showToast('這道菜已經在清單中囉！');
    return;
  }

  const randomEmoji = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
  foods.push({ name, emoji: randomEmoji });
  foodInput.value = '';
  saveAndRender();
  showToast(`已新增 ${name}！`);
}

function saveAndRender() {
  localStorage.setItem('food-list', JSON.stringify(foods));
  renderFoodList();
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove('hidden');
  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3000);
}

// Decision Logic
let isSpinning = false;

function pickRandom() {
  if (isSpinning) return;
  
  isSpinning = true;
  decideBtn.disabled = true;
  resultCard.classList.add('spinning');
  
  let counter = 0;
  const spinInterval = setInterval(() => {
    const tempPick = foods[Math.floor(Math.random() * foods.length)];
    resultText.textContent = tempPick.name;
    resultEmoji.textContent = tempPick.emoji;
    counter++;
    
    if (counter > 20) {
      clearInterval(spinInterval);
      finalizePick();
    }
  }, 100);
}

function finalizePick() {
  const finalPick = foods[Math.floor(Math.random() * foods.length)];
  resultText.textContent = finalPick.name;
  resultEmoji.textContent = finalPick.emoji;
  
  resultCard.classList.remove('spinning');
  isSpinning = false;
  decideBtn.disabled = false;
  
  // Flash effect
  resultCard.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
  setTimeout(() => {
    resultCard.style.backgroundColor = '';
  }, 200);
}

// Event Listeners
decideBtn.addEventListener('click', pickRandom);

addBtn.addEventListener('click', addFood);
foodInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') addFood();
});

addToggle.addEventListener('click', () => {
  addForm.classList.toggle('hidden');
  addToggle.textContent = addForm.classList.contains('hidden') ? '+' : '-';
  if (!addForm.classList.contains('hidden')) foodInput.focus();
});

// Run
init();
