"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Bot, User, ArrowLeft, MoreVertical, Trash2 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface Message {
    id: string
    role: "user" | "ai"
    content: string
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "welcome",
            role: "ai",
            content: "Hello! I'm your AI Financial Analyst. I've analyzed your latest transaction data. How can I help you today?"
        }
    ])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input
        }

        setMessages(prev => [...prev, userMessage])
        setInput("")
        setIsLoading(true)

        // Create placeholder for AI response
        const aiMessageId = (Date.now() + 1).toString()
        setMessages(prev => [...prev, {
            id: aiMessageId,
            role: "ai",
            content: ""
        }])

        try {
            const response = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage.content })
            })

            if (!response.ok) throw new Error("Network response was not ok")
            if (!response.body) throw new Error("No response body")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let aiContent = ""

            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                const chunk = decoder.decode(value, { stream: true })
                aiContent += chunk

                setMessages(prev => prev.map(msg =>
                    msg.id === aiMessageId
                        ? { ...msg, content: aiContent }
                        : msg
                ))
            }
        } catch (error) {
            console.error("Chat error:", error)
            setMessages(prev => prev.map(msg =>
                msg.id === aiMessageId
                    ? { ...msg, content: "Sorry, I encountered an error connecting to the financial brain." }
                    : msg
            ))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#09090b] text-white p-4 md:p-8 flex flex-col items-center">
            <div className="w-full max-w-4xl flex-1 flex flex-col h-[calc(100vh-4rem)]">

                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <Link href="/" className="flex items-center text-zinc-400 hover:text-white transition-colors">
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Dashboard
                    </Link>
                    <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-sm font-medium text-emerald-500">Analyst Active</span>
                    </div>
                </div>

                {/* Chat Window */}
                <Card className="flex-1 glass-panel border-white/5 flex flex-col overflow-hidden relative">
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                        {messages.map((message) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={cn(
                                    "flex w-full items-start gap-4",
                                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                                )}
                            >
                                <div className={cn(
                                    "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                                    message.role === "ai" ? "bg-emerald-500/10 text-emerald-400" : "bg-blue-500/10 text-blue-400"
                                )}>
                                    {message.role === "ai" ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
                                </div>

                                <div className={cn(
                                    "rounded-2xl p-4 max-w-[80%] text-sm leading-relaxed",
                                    message.role === "ai"
                                        ? "bg-white/5 text-zinc-100 border border-white/5"
                                        : "bg-blue-600 text-white"
                                )}>
                                    {message.content || (isLoading && message.id === messages[messages.length - 1].id ? (
                                        <span className="flex space-x-1 items-center h-5">
                                            <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                            <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                            <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce"></span>
                                        </span>
                                    ) : "")}
                                </div>
                            </motion.div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t border-white/10 bg-black/20 backdrop-blur-md">
                        <form onSubmit={handleSubmit} className="relative flex items-center">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about your net worth, top spenders, or budget..."
                                className="w-full bg-white/5 border border-white/10 rounded-full py-4 pl-6 pr-14 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all font-medium"
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="absolute right-2 p-2 bg-emerald-500 hover:bg-emerald-600 rounded-full text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send className="h-4 w-4" />
                            </button>
                        </form>
                        <div className="text-center mt-2">
                            <p className="text-[10px] text-zinc-600">AI can make mistakes. Review financial data manually.</p>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    )
}
