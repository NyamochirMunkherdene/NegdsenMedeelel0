
//const varaibles
const newsdetails = document.getElementById("newsdetails");
const newsType = document.getElementById("newsType");

const usDulaanBtn = document.getElementById("UsDulaan");
const eruulMendBtn = document.getElementById("EruulMend");
const sportBtn = document.getElementById("sport");
const holidayBtn = document.getElementById("holiday");
const oronNutgiinBtn = document.getElementById("oron-nutgiiin-medee");
const zarBtn = document.getElementById("Ad");
const busadBtn = document.getElementById("busad");

const searchBtn = document.getElementById("searchBtn");
const newsQuery = document.getElementById("newsQuery");
const pageInfo = document.getElementById("pageInfo");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");


const categories = {
    UsDulaan: { mn: "yс дулаан, шугам сүлжээний мэдэгдэл", en: "municipal utility announcements" },
    EruulMend: { mn: "эрүүл мэнд", en: "health" },
    sport: { mn: "спорт, тэмцээн", en: "sport, competition" },
    holiday: { mn: "баярын мэндчилгээ", en: "holiday greetings" },
    "oron-nutgiiin-medee": { mn: "орон нутгийн мэдээ", en: "community news" },
    Ad: { mn: "зар, сурталчилгаа", en: "advertisement, promotion" },
    busad: { mn: "бусад", en: "others" }
};


let newsDataArr = [];
let currentPage = 1;
let allNews = [];
const postsPerPage = 20;
let currentLang = "mn"; // Default language


json_path="datas/translated_posts.json"


window.onload = function () {
    newsType.textContent = "Headlines";
    fetchGeneralNews();
};




document.addEventListener("DOMContentLoaded", () => {
    // 1. Detect language based on URL
    currentLang = window.location.pathname.includes("en.html") ? "en" : "mn";
    document.documentElement.lang = currentLang;

    // 2. Set default headline title
    newsType.textContent = currentLang === "en" ? "Headlines" : "Facebook Medee";

    // 3. Load news data
    fetchGeneralNews();

    // 4. Setup Category Event Listeners dynamically
    setupCategoryListeners();

    // 5. Setup Search Button logic safely here!
    const searchBtnElement = document.getElementById("searchBtn"); 
    if (searchBtnElement) {
        console.log("Search button found and listener attached!");
        searchBtnElement.addEventListener("click", function() {
            const queryText = newsQuery.value.trim();
            newsType.innerHTML = `<h4>${currentLang === "en" ? "Search" : "Хайлт"}: ${newsQuery.value}</h4>`;
            console.log(newsQuery.value);
            fetchQueryNews();
        });
    } else {
        console.error("Critical: Could not find an element with id='searchBtn' in the HTML.");
    }
});




// Loop through your categories map to attach listeners smoothly
function setupCategoryListeners() {
    Object.keys(categories).forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener("click", (e) => {
                //e.preventDefault(); //using it
                const categoryObj = categories[id];
                
                
                // Display heading based on active language
                newsType.innerHTML = `<h4>${categoryObj[currentLang]}</h4>`;

                fetchNews(categoryObj[currentLang]);
            });
        }
    });
}




async function fetchNews(categoryKey){
    newsDataArr=[]

    try {
        
        const response = await fetch(json_path);
        if (!response.ok) throw new Error("Couldn't load JSON");
        newsDataArr = await response.json();
        console.log(categoryKey)

        allNews = newsDataArr.filter(news => {
            const recordLabel = currentLang==="en"
            ? news.label_en
            : news.classification.primary_label;
            console.log(recordLabel)
            console.log(categoryKey)



            return recordLabel === categoryKey;
        });
        console.log(allNews)

        currentPage = 1;
        displayNews();


    } catch (error) {
        console.log(error);
        newsdetails.innerHTML = "<h3>Couldn't load news.</h3>";

    }

}



async function fetchGeneralNews() {
    newsDataArr=[];

    try {

        const response = await fetch(json_path);

        if (!response.ok) {throw new Error("Couldn't load JSON");}

        newsDataArr = await response.json();

        currentPage = 1;
        allNews = newsDataArr;
        displayNews();

    } catch (error) {

        console.log(error);
        newsdetails.innerHTML = "<h3>Couldn't load news.</h3>";

    }

}

async function fetchQueryNews(){
    try {
        if (newsDataArr.length === 0) {
            const response = await fetch(json_path);
            if (!response.ok) throw new Error("Couldn't load JSON");
            newsDataArr = await response.json();
        }

        const searchText = newsQuery.value.trim().toLowerCase();

        allNews = newsDataArr.filter(news => {
            // Adjust property targets if your translation structure keys fields differently (e.g., news.post_content_en)
            const targetContent = currentLang === "en" ? news.post_content_en : news.post_content;
            const targetLabel = currentLang === "en" ? news.label_en : news.classification.primary_label;

            return (
                (targetContent && targetContent.toLowerCase().includes(searchText)) ||
                (targetLabel && targetLabel.toLowerCase().includes(searchText))
            );
        });

        currentPage = 1;
        displayNews();
    } catch (error) {
        console.error(error);
        newsdetails.innerHTML = `<h3>${currentLang === "en" ? "Could not find the news." : "Мэдээ олдсонгүй."}</h3>`;
    }
}



function displayNews() {

    newsdetails.innerHTML = "";

    const start = (currentPage - 1) * postsPerPage;
    const end = start + postsPerPage;

    allNews.slice(start, end).forEach(news => {

        const card = document.createElement("div");
        card.className = "card";

        card.innerHTML = `
            <h3>${news.page_name || "News"}</h3>
            <p class="text-muted small">${news.post_date || ""}</p>
            <p>${currentLang === "en" ? news.post_content_en : news.post_content}</p>
            <p><strong>${currentLang === "en" ? "Category" : "Ангилал"}:</strong> ${currentLang === "en" ? news.label_en: news.classification.primary_label}</p>
            <a href="${news.post_url}" target="_blank" class="btn btn-sm btn-outline-warning w-25">
                ${currentLang === "en" ? "Read Original Post" : "Эх сурвалж үзэх"}
            </a>
        `;

        newsdetails.appendChild(card);
    });

    pageInfo.textContent = currentLang === "en" 
        ? `Page ${currentPage} of ${Math.ceil(allNews.length / postsPerPage)}`
        : `Хуудас ${currentPage} / ${Math.ceil(allNews.length / postsPerPage)}`;
}




nextBtn.onclick = () => {
    if(currentPage * postsPerPage < allNews.length){
        currentPage++;
        displayNews();
    }
};

prevBtn.onclick = () => {
    if(currentPage > 1){
        currentPage--;
        displayNews();
    }
};


// 2. Function to switch language and update DOM
function switchLanguage(lang) {
    // Save preference to browser storage
    localStorage.setItem('selectedLanguage', lang);
    
    // Update the HTML 'lang' attribute for accessibility
    document.documentElement.lang = lang;

    // Find all elements that need translation
    const elements = document.querySelectorAll('[data-key]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-key');
        if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
}