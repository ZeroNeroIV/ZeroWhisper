import type { ReactNode, HTMLAttributes } from 'react'

interface TableProps extends HTMLAttributes<HTMLTableElement> { children: ReactNode }
interface TableHeaderProps extends HTMLAttributes<HTMLTableSectionElement> { children: ReactNode }
interface TableBodyProps extends HTMLAttributes<HTMLTableSectionElement> { children: ReactNode }
interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> { children: ReactNode }
interface TableCellProps extends HTMLAttributes<HTMLTableCellElement> { children?: ReactNode }

export function Table({ className = '', children, ...props }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full border-collapse ${className}`} {...props}>{children}</table>
    </div>
  )
}

export function TableHeader({ className = '', children, ...props }: TableHeaderProps) {
  return <thead className={className} {...props}>{children}</thead>
}

export function TableBody({ className = '', children, ...props }: TableBodyProps) {
  return <tbody className={className} {...props}>{children}</tbody>
}

export function TableRow({ className = '', children, ...props }: TableRowProps) {
  return <tr className={`border-b border-[var(--elevation-1-border)] ${className}`} {...props}>{children}</tr>
}

export function TableHeaderCell({ className = '', children, ...props }: TableCellProps) {
  return (
    <th
      className={`label-caps text-[var(--on-surface-variant)] px-3 py-2.5 text-left font-normal ${className}`}
      {...props}
    >
      {children}
    </th>
  )
}

export function TableCell({ className = '', children, ...props }: TableCellProps) {
  return (
    <td className={`px-3 py-2.5 text-sm text-[var(--on-surface)] ${className}`} {...props}>
      {children}
    </td>
  )
}
