import { Card } from '@/components/ui/Card'

export function AboutTab() {
  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="text-lg font-semibold mb-1">ZeroWhisper</h3>
        <p className="text-sm text-muted-foreground mb-4">Version 0.2.0</p>
        <p className="text-sm text-muted-foreground mb-4">
          Self-hosted personal financial manager with encrypted storage.
        </p>
        <div>
          <p className="mb-2 text-sm font-semibold">Tech Stack</p>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>FastAPI</li>
            <li>SQLCipher</li>
            <li>React</li>
            <li>Custom design system</li>
            <li>OpenAI / Google Gemini</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}
