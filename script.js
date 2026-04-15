// JavaScript לאתר תרומות

// נתונים מקומיים (בפרויקט אמיתי זה יהיה בשרת)
let totalRaised = 12500;
let totalDonors = 47;
let familiesHelped = 8;

// בחירת כמות תרומה
document.querySelectorAll('.amount-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // הסרת בחירה קודמת
        document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('selected'));
        
        // בחירת הכפתור הנוכחי
        this.classList.add('selected');
        
        // עדכון השדה
        const amount = this.getAttribute('data-amount');
        document.getElementById('customAmount').value = amount;
    });
});

// טיפול בטופס תרומה
document.getElementById('donationForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const amount = document.getElementById('customAmount').value;
    const name = document.getElementById('donorName').value;
    const email = document.getElementById('donorEmail').value;
    const message = document.getElementById('message').value;
    
    if (!amount || amount < 10) {
        alert('אנא בחרו סכום תרומה של לפחות 10 ש״ח');
        return;
    }
    
    if (!name || !email) {
        alert('אנא מלאו את כל השדות הנדרשים');
        return;
    }
    
    // סימולציה של תרומה מוצלחת
    simulateDonation(parseInt(amount), name, email, message);
});

// סימולציה של תרומה
function simulateDonation(amount, name, email, message) {
    // הצגת הודעת טעינה
    const donateBtn = document.querySelector('.donate-btn');
    const originalText = donateBtn.textContent;
    donateBtn.textContent = 'מעבד תרומה...';
    donateBtn.disabled = true;
    
    // סימולציה של זמן עיבוד
    setTimeout(() => {
        // עדכון הנתונים
        totalRaised += amount;
        totalDonors += 1;
        
        if (totalRaised > (familiesHelped * 1500)) {
            familiesHelped += 1;
        }
        
        // עדכון התצוגה
        updateStats();
        
        // הודעת הצלחה
        showSuccessMessage(amount, name);
        
        // איפוס הטופס
        document.getElementById('donationForm').reset();
        document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('selected'));
        
        // החזרת הכפתור למצב רגיל
        donateBtn.textContent = originalText;
        donateBtn.disabled = false;
        
    }, 2000);
}

// עדכון הסטטיסטיקות
function updateStats() {
    document.getElementById('totalRaised').textContent = `₪${totalRaised.toLocaleString()}`;
    document.getElementById('totalDonors').textContent = totalDonors;
    document.getElementById('familiesHelped').textContent = familiesHelped;
    
    // אנימציה של עדכון
    document.querySelectorAll('.number').forEach(num => {
        num.style.transform = 'scale(1.1)';
        num.style.color = '#27ae60';
        setTimeout(() => {
            num.style.transform = 'scale(1)';
            num.style.color = '#3498db';
        }, 500);
    });
}

// הודעת הצלחה
function showSuccessMessage(amount, name) {
    const message = document.createElement('div');
    message.innerHTML = `
        <div style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            z-index: 1000;
            border: 3px solid #27ae60;
        ">
            <h3 style="color: #27ae60; margin-bottom: 1rem;">🎉 תודה רבה ${name}!</h3>
            <p>תרומתך בסך ${amount} ש״ח התקבלה בהצלחה</p>
            <p style="margin-top: 1rem; color: #7f8c8d;">אנחנו נשלח לך אישור במייל</p>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="margin-top: 1rem; padding: 0.5rem 2rem; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer;">
                סגור
            </button>
        </div>
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        " onclick="this.parentElement.remove()"></div>
    `;
    
    document.body.appendChild(message);
}

// עדכון ראשוני של הנתונים
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    
    // אפקט טעינה הדרגתי
    const sections = document.querySelectorAll('section');
    sections.forEach((section, index) => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(50px)';
        
        setTimeout(() => {
            section.style.transition = 'all 0.8s ease-out';
            section.style.opacity = '1';
            section.style.transform = 'translateY(0)';
        }, index * 200);
    });
});

// אנימציה של מספרים בגלילה
function animateNumbers() {
    const numbers = document.querySelectorAll('.number');
    numbers.forEach(num => {
        const rect = num.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            num.style.animation = 'none';
            setTimeout(() => {
                num.style.animation = 'countUp 2s ease-out';
            }, 10);
        }
    });
}

// CSS לאנימציות
const style = document.createElement('style');
style.textContent = `
    @keyframes countUp {
        from { transform: scale(0.8); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
`;
document.head.appendChild(style);

// האזנה לגלילה
window.addEventListener('scroll', animateNumbers);