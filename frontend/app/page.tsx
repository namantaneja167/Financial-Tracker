"use client"

import { useState, useEffect } from "react"
import { BentoGrid } from "@/components/BentoGrid"
import { TransactionTable } from "@/components/TransactionTable"
import { StatsData, Transaction } from "@/types"
import Link from "next/link"
import { Bot, Download, CreditCard, Target, Calendar, Briefcase, Loader2, Upload } from "lucide-react"
import { toast } from "sonner"

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [stats, setStats] = useState<StatsData | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])

  const loadData = async () => {
    try {
      const [statsRes, txnsRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/stats"),
        fetch("http://127.0.0.1:8000/api/transactions")
      ])

      if (statsRes.ok) setStats(await statsRes.json())
      if (txnsRes.ok) setTransactions(await txnsRes.json())
    } catch (e) {
      console.error("Failed to load data", e)
      toast.error("Failed to load dashboard data. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => { loadData() }, [])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return
    const file = e.target.files[0]
    setUploading(true)

    const formData = new FormData()
    formData.append("file", file)

    // Determine type (simple extension check)
    const type = file.name.endsWith(".csv") ? "csv" : "pdf"

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/upload?type=${type}`, {
        method: "POST",
        body: formData
      })

      if (!res.ok) throw new Error(await res.text())

      const result = await res.json()
      toast.dismiss()
      toast.success(`Imported ${result.inserted} transactions from ${file.name}!`)
      loadData() // Refresh dashboard
    } catch (err: any) {
      console.error(err)
      toast.error("Upload failed: " + (err.detail || err.message))
    } finally {
      setUploading(false)
      // Reset input
      e.target.value = ""
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground p-6 md:p-12 relative overflow-hidden">
      {/* Ambient Background Effects */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px]" />
      </div>

      <header className="mb-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Financial Tracker
          </h1>
          <p className="text-muted-foreground mt-2">
            Pro Max Dashboard
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/chat"
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 transition-all font-medium text-sm"
          >
            <Bot className="h-4 w-4" />
            Ask AI Analyst
          </Link>
          <Link
            href="/subscriptions"
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 border border-purple-500/20 transition-all font-medium text-sm"
          >
            <CreditCard className="h-4 w-4" />
            Subscriptions
          </Link>
          <Link
            href="/goals"
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition-all font-medium text-sm"
          >
            <Target className="h-4 w-4" />
            Goals
          </Link>
          <Link
            href="/calendar"
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 border border-indigo-500/20 transition-all font-medium text-sm"
          >
            <Calendar className="h-4 w-4" />
            Calendar
          </Link>
          <Link
            href="/portfolio"
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 transition-all font-medium text-sm"
          >
            <Briefcase className="h-4 w-4" />
            Portfolio
          </Link>

          <div className="relative">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.csv"
              onChange={handleFileUpload}
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className={`flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors cursor-pointer ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {uploading ? "Importing..." : "Import Data"}
            </label>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
        </div>
      ) : (
        <>
          <BentoGrid data={stats || { total_income: 0, total_spend: 0, savings_rate: 0, monthly_trend: [] }} />
          <div className="mt-8">
            <TransactionTable initialData={transactions} />
          </div>
        </>
      )}
    </main >
  )
}
