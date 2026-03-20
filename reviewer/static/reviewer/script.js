const state = {
    action: "chat",
    lastAnswer: "",
    lastWarning: "",
    lastModel: "",
    history: [],
    sideView: "reply",
};

const codeEditor = document.getElementById("codeEditor");
const promptInput = document.getElementById("promptInput");
const modelSelect = document.getElementById("modelSelect");
const languageSelect = document.getElementById("languageSelect");
const chatHistory = document.getElementById("chatHistory");
const reviewStatus = document.getElementById("reviewStatus");
const terminalOutput = document.getElementById("terminalOutput");
const workspace = document.querySelector(".workspace");
const replyPreview = document.getElementById("replyPreview");
const terminalView = document.getElementById("terminalView");
const replyView = document.getElementById("replyView");
const sidePanelTitle = document.getElementById("sidePanelTitle");
const showTerminalBtn = document.getElementById("showTerminalBtn");
const showReplyInlineBtn = document.getElementById("showReplyInlineBtn");

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(";").shift();
    }
    return "";
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatInline(text) {
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return formatted;
}

function normalizeAnswerText(text) {
    const trimmed = text.trim();
    const match = trimmed.match(/^```(?:markdown|md)?\n([\s\S]*?)\n```$/i);
    return match ? match[1].trim() : text;
}

function lineIsBullet(line) {
    return /^[-*]\s+/.test(line);
}

function lineIsHeading(line) {
    return /^(#{2,4})\s+/.test(line);
}

function createAnswerCard(label, extraClass = "") {
    const card = document.createElement("section");
    card.className = `answer-card ${extraClass}`.trim();
    if (label) {
        const tag = document.createElement("span");
        tag.className = "answer-label";
        tag.textContent = label;
        card.appendChild(tag);
    }
    return card;
}

async function copyText(text, button) {
    try {
        await navigator.clipboard.writeText(text);
        if (button) {
            const original = button.textContent;
            button.textContent = "Copied";
            button.classList.add("is-copied");
            window.setTimeout(() => {
                button.textContent = original;
                button.classList.remove("is-copied");
            }, 1200);
        }
    } catch (error) {
        setStatus("Copy failed on this browser.");
    }
}

function appendParagraph(container, text) {
    const paragraph = document.createElement("p");
    paragraph.innerHTML = formatInline(text);
    container.appendChild(paragraph);
}

function appendBulletList(container, lines) {
    const card = createAnswerCard("Key Points", "compact-card");
    const list = document.createElement("ul");
    lines.forEach((line) => {
        const item = document.createElement("li");
        item.innerHTML = formatInline(line.replace(/^[-*]\s+/, ""));
        list.appendChild(item);
    });
    card.appendChild(list);
    container.appendChild(card);
}

function appendHeading(container, line) {
    const hashes = line.match(/^(#{2,4})\s+/)[1].length;
    const text = line.replace(/^#{2,4}\s+/, "").trim();
    const card = createAnswerCard(hashes === 2 ? "Section" : "Topic", "heading-card compact-card");
    const heading = document.createElement(hashes === 2 ? "h2" : "h3");
    heading.innerHTML = formatInline(text);
    card.appendChild(heading);
    container.appendChild(card);
}

function appendCodeBlock(container, language, codeLines, sectionTitle = "") {
    const codeText = codeLines.join("\n").trimEnd();
    const card = createAnswerCard("", "section-card code-card compact-card");
    if (sectionTitle) {
        const heading = document.createElement("h3");
        heading.className = "section-title";
        heading.innerHTML = formatInline(sectionTitle);
        card.appendChild(heading);
    }
    const toolbar = document.createElement("div");
    toolbar.className = "code-toolbar";

    const label = document.createElement("span");
    label.className = "answer-label";
    label.textContent = language || "Code";

    const copyButton = document.createElement("button");
    copyButton.className = "copy-btn";
    copyButton.type = "button";
    copyButton.textContent = "Copy Code";
    copyButton.addEventListener("click", () => copyText(codeText, copyButton));

    toolbar.appendChild(label);
    toolbar.appendChild(copyButton);

    const pre = document.createElement("pre");
    pre.className = "answer-code";
    pre.textContent = codeText;
    card.appendChild(toolbar);
    card.appendChild(pre);
    container.appendChild(card);
}

function appendParagraphBlock(container, lines) {
    const text = lines.join(" ").trim();
    if (!text) {
        return;
    }

    const card = createAnswerCard("", "section-card compact-card");
    appendParagraph(card, text);
    container.appendChild(card);
}

function renderAnswerMarkup(text, options = {}) {
    const normalizedText = normalizeAnswerText(text);
    const root = document.createElement("div");
    root.className = "rendered-answer";

    if (options.model || options.warning) {
        const topCard = createAnswerCard(options.model || "Review", `${options.warning ? "warning-card" : "heading-card"} compact-card`);
        if (options.model) {
            const heading = document.createElement("h3");
            heading.textContent = `Model: ${options.model}`;
            topCard.appendChild(heading);
        }
        if (options.warning) {
            appendParagraph(topCard, options.warning);
        }
        root.appendChild(topCard);
    }

    const lines = normalizedText.replace(/\r\n/g, "\n").split("\n");
    let paragraphLines = [];
    let bulletLines = [];
    let inCode = false;
    let codeLanguage = "";
    let codeLines = [];
    let currentSection = null;
    let pendingSectionTitle = "";
    let codeSectionTitle = "";

    const ensureSection = (title = "") => {
        if (!currentSection) {
            currentSection = createAnswerCard("", "section-card compact-card");
            const finalTitle = title || pendingSectionTitle;
            if (finalTitle) {
                const heading = document.createElement("h3");
                heading.className = "section-title";
                heading.innerHTML = formatInline(finalTitle);
                currentSection.appendChild(heading);
                pendingSectionTitle = "";
            }
            root.appendChild(currentSection);
        }
        return currentSection;
    };

    const closeSection = () => {
        currentSection = null;
    };

    const flushParagraph = () => {
        if (paragraphLines.length) {
            const card = ensureSection();
            appendParagraph(card, paragraphLines.join(" ").trim());
            paragraphLines = [];
        }
    };

    const flushBullets = () => {
        if (bulletLines.length) {
            const card = ensureSection();
            const list = document.createElement("ul");
            bulletLines.forEach((line) => {
                const item = document.createElement("li");
                item.innerHTML = formatInline(line.replace(/^[-*]\s+/, ""));
                list.appendChild(item);
            });
            card.appendChild(list);
            bulletLines = [];
        }
    };

    const flushCode = () => {
        if (codeLines.length || codeLanguage) {
            closeSection();
            appendCodeBlock(root, codeLanguage, codeLines, codeSectionTitle);
        }
        codeLines = [];
        codeLanguage = "";
        codeSectionTitle = "";
    };

    lines.forEach((line) => {
        if (line.trim().startsWith("```")) {
            flushParagraph();
            flushBullets();
            if (inCode) {
                flushCode();
            } else {
                closeSection();
                codeLanguage = line.trim().replace("```", "").trim();
                codeSectionTitle = pendingSectionTitle;
                pendingSectionTitle = "";
            }
            inCode = !inCode;
            return;
        }

        if (inCode) {
            codeLines.push(line);
            return;
        }

        if (!line.trim()) {
            flushParagraph();
            flushBullets();
            return;
        }

        if (lineIsHeading(line.trim())) {
            flushParagraph();
            flushBullets();
            closeSection();
            pendingSectionTitle = line.trim().replace(/^#{2,4}\s+/, "").trim();
            return;
        }

        if (lineIsBullet(line.trim())) {
            flushParagraph();
            bulletLines.push(line.trim());
            return;
        }

        if (/^\d+\.\s+/.test(line.trim())) {
            flushParagraph();
            bulletLines.push(`- ${line.trim()}`);
            return;
        }

        paragraphLines.push(line.trim());
    });

    flushParagraph();
    flushBullets();
    if (inCode) {
        flushCode();
    }

    if (!root.children.length) {
        const empty = createAnswerCard("Reply", "section-card compact-card");
        appendParagraph(empty, normalizedText);
        root.appendChild(empty);
    }

    return root;
}

function setStatus(message) {
    reviewStatus.textContent = message;
}

function setSideView(nextView) {
    state.sideView = nextView;
    if (workspace) {
        workspace.dataset.sideView = nextView;
    }
    const terminalActive = nextView === "terminal";
    terminalView.hidden = !terminalActive;
    replyView.hidden = terminalActive;
    sidePanelTitle.textContent = terminalActive ? "Run" : "Review";
    showTerminalBtn.classList.toggle("is-active", terminalActive);
    showReplyInlineBtn.classList.toggle("is-active", !terminalActive);
}

function addMessage(role, content, meta = {}) {
    const article = document.createElement("article");
    article.className = `message ${role}`;

    const title = document.createElement("h3");
    title.textContent = role === "assistant" ? "CodeBuddy" : "You";
    article.appendChild(title);

    if (role === "assistant") {
        article.appendChild(renderAnswerMarkup(content, meta));
    } else {
        const body = document.createElement("p");
        body.className = "message-text";
        body.textContent = content;
        article.appendChild(body);
    }

    chatHistory.appendChild(article);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function updateReplyPreview() {
    replyPreview.innerHTML = "";
    replyPreview.classList.toggle("empty", !state.lastAnswer);

    if (!state.lastAnswer) {
        const emptyState = document.createElement("div");
        emptyState.className = "empty-state";
        emptyState.innerHTML = "<h3>No Reply Yet</h3><p>Generate a review and it will appear here with headings, cards, lists, and code blocks.</p>";
        replyPreview.appendChild(emptyState);
        return;
    }

    replyPreview.appendChild(
        renderAnswerMarkup(state.lastAnswer, {
            model: state.lastModel,
            warning: state.lastWarning,
        })
    );
}

function setAction(nextAction) {
    state.action = nextAction;
    document.querySelectorAll(".action-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.action === nextAction);
    });
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
    });

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }
        return data;
    }

    if (!response.ok) {
        throw new Error("Request failed.");
    }

    return response;
}

async function sendForReview() {
    const prompt = promptInput.value.trim();
    const code = codeEditor.value.trim();

    if (!code) {
        setStatus("Paste code into the editor first.");
        return;
    }

    addMessage("user", prompt || `Run ${state.action} on my current code.`);
    state.history.push({
        role: "user",
        content: prompt || `Run ${state.action} on my current code.`,
    });

    setStatus("Review in progress...");

    try {
        const data = await postJson("/api/review/", {
            action: state.action,
            prompt,
            code,
            model: modelSelect.value,
            language: languageSelect.value,
            history: state.history,
        });

        state.lastAnswer = data.answer;
        state.lastModel = data.model;
        state.lastWarning = data.warning || "";
        state.history.push({ role: "assistant", content: data.answer });

        addMessage("assistant", data.answer, {
            model: data.model,
            warning: data.warning || "",
        });
        updateReplyPreview();
        setSideView("reply");
        setStatus(data.warning || "Review completed.");
        promptInput.value = "";
    } catch (error) {
        addMessage("assistant", `Error: ${error.message}`, {
            model: "system",
            warning: "The request failed before a formatted review could be generated.",
        });
        setStatus(error.message);
    }
}

async function runCode() {
    setStatus("Running code...");
    setSideView("terminal");

    try {
        const data = await postJson("/api/run/", {
            language: languageSelect.value,
            code: codeEditor.value,
        });
        terminalOutput.textContent = data.output;
        setStatus("Execution finished.");
    } catch (error) {
        terminalOutput.textContent = error.message;
        setStatus(error.message);
    }
}

async function downloadPdf() {
    if (!state.lastAnswer) {
        setStatus("Generate a review before exporting the PDF.");
        return;
    }

    setStatus("Creating PDF...");

    try {
        const response = await postJson("/api/report/pdf/", {
            title: "Code Review Report",
            action: state.action,
            language: languageSelect.value,
            answer: state.lastAnswer,
            code: codeEditor.value,
        });
        const blob = await response.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "code-review-report.pdf";
        link.click();
        URL.revokeObjectURL(link.href);
        setStatus("PDF downloaded.");
    } catch (error) {
        setStatus(error.message);
    }
}

function loadSampleCode() {
    codeEditor.value = `def binary_search(nums, target):
    left = 0
    right = len(nums)

    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1

print(binary_search([2, 4, 7, 9, 13], 13))`;
    promptInput.value = "Create a report for this code and explain the bug simply.";
    setAction("create_report");
    setStatus("Sample loaded.");
}

document.querySelectorAll(".action-btn").forEach((button) => {
    button.addEventListener("click", () => setAction(button.dataset.action));
});

document.getElementById("sendBtn").addEventListener("click", sendForReview);
document.getElementById("runBtn").addEventListener("click", runCode);
document.getElementById("downloadBtn").addEventListener("click", downloadPdf);
document.getElementById("sampleBtn").addEventListener("click", loadSampleCode);
document.getElementById("copyEditorBtn").addEventListener("click", async (event) => {
    await copyText(codeEditor.value, event.currentTarget);
});
document.getElementById("clearBtn").addEventListener("click", () => {
    codeEditor.value = "";
    promptInput.value = "";
    setStatus("Editor cleared.");
});
document.getElementById("clearTerminalBtn").addEventListener("click", () => {
    terminalOutput.textContent = "Terminal ready.";
});
showTerminalBtn.addEventListener("click", () => {
    setSideView("terminal");
});
showReplyInlineBtn.addEventListener("click", () => {
    setSideView("reply");
});

promptInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        sendForReview();
    }
});

updateReplyPreview();
setSideView("reply");
