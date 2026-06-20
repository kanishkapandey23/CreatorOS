'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize from 'rehype-sanitize';
import { cn } from '@/lib/utils';

export function MarkdownContent({ children, className }) {
  if (!children || !String(children).trim()) return null;

  return (
    <div className={cn('markdown-content', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeSanitize]}
        components={{
          a: ({ href, children: linkChildren }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="font-medium text-brand underline underline-offset-2 hover:text-brand/80">
              {linkChildren}
            </a>
          ),
          code: ({ inline, className: codeClass, children: codeChildren, ...props }) =>
            inline ? (
              <code className="rounded-md bg-secondary/80 px-1.5 py-0.5 font-mono text-[0.88em] text-ink" {...props}>
                {codeChildren}
              </code>
            ) : (
              <code className={cn('font-mono text-[13px] leading-relaxed', codeClass)} {...props}>
                {codeChildren}
              </code>
            ),
        }}
      >
        {String(children)}
      </ReactMarkdown>
    </div>
  );
}
