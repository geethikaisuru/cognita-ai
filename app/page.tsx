"use client"

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useTheme } from "next-themes"
import { MoonIcon, SunIcon } from "@radix-ui/react-icons"
import { BrainCircuit, ExternalLink } from 'lucide-react'

export default function Home() {
  const [files, setFiles] = useState<File[]>([])
  const [output, setOutput] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const { setTheme, theme } = useTheme()

  useEffect(() => {
    if (isGenerating) {
      const interval = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= 100) {
            clearInterval(interval)
            return 100
          }
          return prevProgress + 10
        })
      }, 500)

      return () => clearInterval(interval)
    }
  }, [isGenerating])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setOutput('')
    setDownloadUrl(null)
    setProgress(0)

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
      setProgress(100)
    }
  }

  return (
    <main className="container mx-auto p-4 relative min-h-screen">
      <div className="absolute top-4 right-4 flex items-center space-x-3">
        <Button
          variant="outline"
          size="icon"
          className="flex items-center space-x-2 w-full mx pl-2 pr-2"
          onClick={() => {}}
        >
          <BrainCircuit className="h-4 w-4" />
          <span className="text-xs">Ollama Phi 3</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="flex pl-2 pr-2 "
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <SunIcon className="h-[1.2rem] w-[1.2rem]" /> : <MoonIcon className="h-[1.2rem] w-[1.2rem]" />}
          <span className="sr-only ">Toggle theme</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="flex items-center space-x-1 max-w-[6rem] w-full mx pl-2 pr-2"
          onClick={() => window.open("https://github.com/geethikaisuru", "_blank")}
        >
          <span className="text-xs">About Me</span>
          <ExternalLink className="h-4 w-4" />
        </Button>
      </div>

      <h1 className="text-2xl font-bold mb-4 mt-16"><b>Cognita.ai</b> - Model Paper Generator</h1>
      <Card>
        <CardHeader>
          <CardTitle>Upload your Past Paper PDF Files</CardTitle>
        </CardHeader>
        <CardContent>
          <Input type="file" multiple onChange={handleFileChange} accept=".pdf" />
          <Button onClick={handleGenerate} disabled={isGenerating || files.length === 0} className="mt-2">
            {isGenerating ? 'Generating...' : 'Generate Model Paper'}
          </Button>
          {isGenerating && (
            <div className="mt-4">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-center mt-2">Generating file... {progress}%</p>
            </div>
          )}
        </CardContent>
      </Card>
      {output && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Output</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap">{output}</pre>
            {downloadUrl && (
              <Button asChild className="mt-4">
                <a href={downloadUrl} download="model_paper.pdf">Download Model Paper</a>
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </main>
  )
}