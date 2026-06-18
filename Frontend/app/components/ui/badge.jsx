import * as React from "react"

export function Badge({ className, variant, ...props }) {
  let variantClass = "bg-secondary text-ink border-transparent"
  if (variant === "outline") {
    variantClass = "border border-line text-ink-muted bg-transparent"
  } else if (variant === "destructive" || variant === "danger") {
    variantClass = "bg-danger-soft text-danger border-transparent"
  }
  
  return (
    <div
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variantClass} ${className || ""}`}
      {...props}
    />
  )
}
