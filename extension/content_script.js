
// Map of hostname to scraping logic
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

// --- Scraper Implementations ---

function scrapeChatGPT() {
    console.log("Scraping ChatGPT...");
    const conversation = [];

    // Strategy 1: [data-message-author-role] (Best)
    let messages = document.querySelectorAll('[data-message-author-role]');

    // Strategy 2: If none, look for .text-message (Historical)
    if (messages.length === 0) {
        messages = document.querySelectorAll('.text-message, .message');
    }

    // Strategy 3: Articles (Old)
    if (messages.length === 0) {
        messages = document.querySelectorAll('article');
    }

    messages.forEach(msg => {
        // Role
        let role = 'model';
        const roleAttr = msg.getAttribute('data-message-author-role');
        if (roleAttr === 'user') role = 'user';
        else if (roleAttr === 'assistant') role = 'model';
        else {
            // Heuristic if attr missing
            // Search for "You" or user avatar presence? Hard to generalize.
            // Assume model if not explicitly user?
            if (msg.querySelector('.font-user-message') || msg.innerText.startsWith('You\n')) role = 'user';
        }

        // Content
        // Try multiple selectors for the text content
        const contentNode = msg.querySelector('.markdown') ||
            msg.querySelector('.whitespace-pre-wrap') ||
            msg.querySelector('.text-base') ||
            msg;

        const content = contentNode.innerText.trim();

        if (content) {
            // Deduplicate?
            conversation.push({ role, content });
        }
    });

    console.log(`Scraped ${conversation.length} messages.`);
    return { conversation: conversation };
}

function scrapeGemini() {
    console.log("Scraping Gemini...");
    const conversation = [];
    // Select all potential conversation blocks
    const userSelectors = '.user-query-container, [data-test-id="user-query"]';
    const modelSelectors = '.model-response-container, [data-test-id="model-response"]';

    // Attempt to select all in order
    const allBlocks = document.querySelectorAll(`${userSelectors}, ${modelSelectors}`);

    if (allBlocks.length === 0) {
        // Fallback: old Gemini layout might use different classes
        const messages = document.querySelectorAll('.message-content');
        messages.forEach(msg => {
            // Heuristic to detect role? Difficult without containers.
            // Check for icon? 
            conversation.push({ role: 'model', content: msg.innerText.trim() }); // Default to model
        });
    } else {
        allBlocks.forEach(block => {
            let role = 'model';
            if (block.matches(userSelectors) || block.querySelector(userSelectors)) {
                role = 'user';
            }
            const text = block.innerText.trim();
            if (text) conversation.push({ role, content: text });
        });
    }

    return { conversation: conversation };
}


function scrapePerplexity() {
    console.log("Scraping Perplexity...");
    const conversation = [];

    const main = document.querySelector('main');
    if (!main) return { conversation: [] };

    // Perplexity User Query is often in an H1 or a specific class at the top
    // Followed by the answer in a .prose div.
    // Follow-up queries are also headers or specific divs.

    // Strategy: structural iteration
    // User query: h1, .font-display
    // Model answer: .prose

    // We try to grab them in document order.
    // Note: Perplexity often displays the "Answer" header, "Sources" etc. We want the PROSE content.

    // Select all relevant nodes
    const nodes = main.querySelectorAll('h1, .font-display, .prose');

    nodes.forEach(node => {
        let role = 'model';
        let content = node.innerText.trim();

        // Filter out UI headers like "Sources", "Related"
        if (['Sources', 'Related', 'Answer'].includes(content)) return;

        if (node.tagName === 'H1') {
            role = 'user';
        } else if (node.classList.contains('font-display')) {
            role = 'user'; // Follow up questions often use this font
        } else if (node.classList.contains('prose')) {
            role = 'model';
        }

        // Heuristic: User queries are usually short? Not necessarily.

        if (content) {
            // Avoid duplicate pushes if nested (unlikely with this selector set)
            conversation.push({ role, content });
        }
    });

    return { conversation: conversation };
}

function scrapeClaude() {
    console.log("Scraping Claude...");
    const conversation = [];

    // Claude conversation container
    const messages = document.querySelectorAll('.font-claude-message, .font-user-message');

    if (messages.length === 0) {
        // Fallback selectors
        const allDivs = document.querySelectorAll('[data-testid="user-message"], [data-testid="claude-message"]');
        allDivs.forEach(div => {
            const role = div.getAttribute('data-testid') === 'user-message' ? 'user' : 'model';
            conversation.push({ role, content: div.innerText.trim() });
        });
    } else {
        messages.forEach(msg => {
            let role = 'model';
            if (msg.classList.contains('font-user-message')) {
                role = 'user';
            }
            // Double check parents for "User" label if class is vague
            // logic...

            conversation.push({ role, content: msg.innerText.trim() });
        });
    }

    return { conversation };
}


function scrapeDeepseek() {
    console.log("Scraping Deepseek...");
    const conversation = [];
    const messages = document.querySelectorAll('.ds-message, .message'); // Hypothetical classes
    // Deepseek is new/variable. 
    // Fallback: grab all text in main container?
    return { conversation: [] };
}


// --- Execution ---

try {
    const scraper = getScraper();
    if (!scraper) {
        console.warn("No scraper found for:", window.location.hostname);
        // Explicitly return an error object so popup knows it's unsupported vs failed
        ({ error: "Hostname not supported: " + window.location.hostname });
    } else {
        const data = scraper();
        console.log("Final Scrape Data:", data);
        data; // Return to popup
    }
} catch (e) {
    console.error("Scraping error:", e);
    ({ error: "Script Error: " + e.message });
}
