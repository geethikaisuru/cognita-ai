"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  const [files, setFiles] = useState<File[]>([])
  const [output, setOutput] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setOutput('')
    setDownloadUrl(null)

    try {
      const filePromises = files.map(file => {
        return new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onloadend = () => resolve(reader.result as string)
          reader.onerror = reject
          reader.readAsDataURL(file)
        })
      })

      const base64Files = await Promise.all(filePromises)

      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ files: base64Files.map(f => f.split(',')[1]) }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Generation failed')
      }

      const data = await response.json()
      const base64Pdf = data.pdf

      if (!base64Pdf) {
        throw new Error('No PDF data received from the server')
      }

      const blob = new Blob([Buffer.from(base64Pdf, 'base64')], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)

      setDownloadUrl(url)
      setOutput('Generation completed successfully. Click the download button to get your PDF.')
    } catch (error) {
      console.error('Error:', error)
      setOutput(`An error occurred during generation: ${error.message}`)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <main className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Model Paper Generator</h1>
      <Card>
        <CardHeader>
          <CardTitle>Upload PDF Files</CardTitle>
        </CardHeader>
        <CardContent>
          <Input type="file" multiple onChange={handleFileChange} accept=".pdf" />
          <Button onClick={handleGenerate} disabled={isGenerating || files.length === 0} className="mt-2">
            {isGenerating ? 'Generating...' : 'Generate Model Paper'}
          </Button>
        </CardContent>
      </Card>
      {output && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Output</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap">{output}</pre>
          </CardContent>
        </Card>
      )}
      {downloadUrl && (
        <Button asChild className="mt-4">
          <a href={downloadUrl} download="model_paper.pdf">Download Model Paper</a>
        </Button>
      )}
    </main>
  )
}