document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    // Auto-expand textarea
    userInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
        if (this.value === "") {
            this.style.height = "auto";
        }
    });

    // Send on Enter (Shift+Enter for new line)
    userInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener("click", sendMessage);

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // 1. Show user message
        appendMessage(text, "user");
        userInput.value = "";
        
        // NOTE: We DO NOT show the loading bubble here anymore!
        
        // Add a basic typing indicator for the AI (optional, but good for UX)
        const typingIndicator = document.createElement("div");
        typingIndicator.id = "general-typing";
        typingIndicator.className = "text-gray-400 text-sm mt-2 ml-4";
        typingIndicator.textContent = "AI is thinking...";
        chatContainer.appendChild(typingIndicator);
        scrollToBottom();

        try {
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: text })
            });
            
            // 2. Read the live stream from FastAPI
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                // Decode the chunk of data sent by the backend
                const chunkText = decoder.decode(value);
                const dataLines = chunkText.trim().split("\n");
                
                for (const line of dataLines) {
                    if (!line) continue;
                    const data = JSON.parse(line);
                    
                    // 3. React to the specific events!
                    if (data.type === "tool_start") {
                        document.getElementById("general-typing")?.remove();
                        showLoading(); // ONLY trigger the tool bubble when the backend says so!
                    } 
                    else if (data.type === "final_answer") {
                        document.getElementById("general-typing")?.remove();
                        removeLoading(); // Kill the tool bubble
                        appendMessage(data.content, "ai"); // Show the final math
                    }
                }
            }
        } catch (error) {
            document.getElementById("general-typing")?.remove();
            removeLoading();
            appendMessage("Sorry, I encountered a network error.", "error");
        }
    }

    function appendMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `flex flex-col items-${sender === 'user' ? 'end' : 'start'} mt-6 animate-fade-in`;
        
        const bubble = document.createElement("div");
        
        if (sender === "user") {
            // User messages stay plain text
            bubble.className = "bg-blue-50 text-blue-900 border border-blue-100 px-5 py-3 rounded-2xl rounded-tr-none max-w-[85%] leading-relaxed whitespace-pre-wrap";
            bubble.textContent = text;
        } else if (sender === "error") {
            bubble.className = "bg-red-50 text-red-600 border border-red-200 px-5 py-3 rounded-2xl rounded-tl-none max-w-[85%] leading-relaxed";
            bubble.textContent = text;
        }  else {
            // AI messages
            bubble.className = "prose prose-sm md:prose-base bg-white text-gray-800 border border-gray-100 shadow-sm px-5 py-3 rounded-2xl rounded-tl-none max-w-[85%] leading-relaxed";
            
            // --- THE REGEX SHIELD ---
            // 1. Convert \( \) to $ and \[ \] to $$ (Marked.js ignores $ symbols)
            let safeText = text
                .replace(/\\\[/g, '$$$$') 
                .replace(/\\\]/g, '$$$$') 
                .replace(/\\\(/g, '$')   
                .replace(/\\\)/g, '$');  
            
            // 2. Convert Markdown to HTML
            bubble.innerHTML = marked.parse(safeText);
            
            // 3. Tell MathJax to scan and render the protected LaTeX
            if (window.MathJax) {
                MathJax.typesetPromise([bubble]).catch(function (err) {
                    console.error("MathJax error:", err.message);
                });
            }
        }

        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function showLoading() {
    const msgDiv = document.createElement("div");
    msgDiv.id = "tool-loading-bubble";
    msgDiv.className = "flex flex-col items-start mt-6 animate-fade-in";
    msgDiv.innerHTML = `
        <div class="bg-gray-50 text-gray-500 border border-gray-200 px-5 py-3 rounded-2xl rounded-tl-none text-sm flex items-center gap-3">
            <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Calling Python tool...
        </div>
    `;
    chatContainer.appendChild(msgDiv);
    scrollToBottom();
    }

    function removeLoading() {
        const loadingBubble = document.getElementById("tool-loading-bubble");
        if (loadingBubble) {
            loadingBubble.remove();
        }
    }

    function showTypingIndicator() {
        const id = "typing-" + Date.now();
        const msgDiv = document.createElement("div");
        msgDiv.id = id;
        msgDiv.className = "flex flex-col items-start mt-6";
        
        const bubble = document.createElement("div");
        bubble.className = "bg-white border border-gray-100 shadow-sm px-5 py-4 rounded-2xl rounded-tl-none flex items-center";
        bubble.innerHTML = `
            <div class="typing-indicator flex items-center">
                <span></span><span></span><span></span>
            </div>
        `;
        
        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: "smooth"
        });
    }
});