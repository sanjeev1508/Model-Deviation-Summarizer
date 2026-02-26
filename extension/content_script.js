(() => {
    // ── Scraper map ──────────────────────────────────────────────────────────
    const SCRAPERS = {
        'chatgpt.com': scrapeChatGPT,
        'gemini.google.com': scrapeGemini,
        'perplexity.ai': scrapePerplexity,
        'claude.ai': scrapeClaude,
        'deepseek.com': scrapeDeepseek
    };

    function getScraper() {
        const hostname = window.location.hostname;
        console.log("Detecting scraper for:", hostname);
        for (const key in SCRAPERS) {
            if (hostname.includes(key)) return SCRAPERS[key];
        }
        return null;
    }

    // ── Scraper Implementations ──────────────────────────────────────────────

    function scrapeChatGPT() {
        console.log("Scraping ChatGPT...");
        const conversation = [];

        let messages = document.querySelectorAll('[data-message-author-role]');
        if (messages.length === 0) messages = document.querySelectorAll('.text-message, .message');
        if (messages.length === 0) messages = document.querySelectorAll('article');

        messages.forEach(msg => {
            let role = 'model';
            const roleAttr = msg.getAttribute('data-message-author-role');
            if (roleAttr === 'user') role = 'user';
            else if (roleAttr === 'assistant') role = 'model';
            else {
                if (msg.querySelector('.font-user-message') || msg.innerText.startsWith('You\n')) role = 'user';
            }

            const contentNode = msg.querySelector('.markdown') ||
                msg.querySelector('.whitespace-pre-wrap') ||
                msg.querySelector('.text-base') ||
                msg;

            const content = contentNode.innerText.trim();
            if (content) conversation.push({ role, content });
        });

        console.log(`Scraped ${conversation.length} messages.`);
        return { conversation };
    }

    function scrapeGemini() {
        console.log("Scraping Gemini...");
        const conversation = [];
        const userSelectors = '.user-query-container, [data-test-id="user-query"]';
        const modelSelectors = '.model-response-container, [data-test-id="model-response"]';
        const allBlocks = document.querySelectorAll(`${userSelectors}, ${modelSelectors}`);

        if (allBlocks.length === 0) {
            document.querySelectorAll('.message-content').forEach(msg => {
                conversation.push({ role: 'model', content: msg.innerText.trim() });
            });
        } else {
            allBlocks.forEach(block => {
                let role = 'model';
                if (block.matches(userSelectors) || block.querySelector(userSelectors)) role = 'user';
                const text = block.innerText.trim();
                if (text) conversation.push({ role, content: text });
            });
        }
        return { conversation };
    }

    function scrapePerplexity() {
        console.log("Scraping Perplexity...");
        const conversation = [];
        const main = document.querySelector('main');
        if (!main) return { conversation: [] };

        main.querySelectorAll('h1, .font-display, .prose').forEach(node => {
            const content = node.innerText.trim();
            if (['Sources', 'Related', 'Answer'].includes(content)) return;

            let role = 'model';
            if (node.tagName === 'H1' || node.classList.contains('font-display')) role = 'user';

            if (content) conversation.push({ role, content });
        });
        return { conversation };
    }

    function scrapeClaude() {
        console.log("Scraping Claude...");
        const conversation = [];
        const messages = document.querySelectorAll('.font-claude-message, .font-user-message');

        if (messages.length === 0) {
            document.querySelectorAll('[data-testid="user-message"], [data-testid="claude-message"]').forEach(div => {
                const role = div.getAttribute('data-testid') === 'user-message' ? 'user' : 'model';
                conversation.push({ role, content: div.innerText.trim() });
            });
        } else {
            messages.forEach(msg => {
                const role = msg.classList.contains('font-user-message') ? 'user' : 'model';
                conversation.push({ role, content: msg.innerText.trim() });
            });
        }
        return { conversation };
    }

    function scrapeDeepseek() {
        console.log("Scraping Deepseek...");
        const conversation = [];
        document.querySelectorAll('.ds-message-container, [class*="user"], [class*="assistant"]').forEach(msg => {
            const isUser = msg.className.includes('user');
            const content = msg.innerText.trim();
            if (content) conversation.push({ role: isUser ? 'user' : 'model', content });
        });
        return { conversation };
    }

    // ── Execution ────────────────────────────────────────────────────────────
    try {
        const scraper = getScraper();
        if (!scraper) {
            console.warn("No scraper found for:", window.location.hostname);
            return { error: "Hostname not supported: " + window.location.hostname };
        }
        const data = scraper();
        console.log("Final Scrape Data:", data);
        return data;
    } catch (e) {
        console.error("Scraping error:", e);
        return { error: "Script Error: " + e.message };
    }
})();
