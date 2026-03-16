import {
  Box,
  Code,
  Divider,
  Link,
  ListItem,
  OrderedList,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  UnorderedList,
} from '@chakra-ui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

const components: Components = {
  p: ({ children }) => (
    <Text fontSize="sm" lineHeight="tall" mb={2}>
      {children}
    </Text>
  ),
  strong: ({ children }) => (
    <Text as="strong" fontWeight="bold">
      {children}
    </Text>
  ),
  em: ({ children }) => (
    <Text as="em" fontStyle="italic">
      {children}
    </Text>
  ),
  a: ({ href, children }) => (
    <Link href={href} color="accent.blue" isExternal>
      {children}
    </Link>
  ),
  ul: ({ children }) => (
    <UnorderedList pl={4} mb={2} fontSize="sm" spacing={0.5}>
      {children}
    </UnorderedList>
  ),
  ol: ({ children }) => (
    <OrderedList pl={4} mb={2} fontSize="sm" spacing={0.5}>
      {children}
    </OrderedList>
  ),
  li: ({ children }) => <ListItem lineHeight="tall">{children}</ListItem>,
  code: ({ className, children }) => {
    const isBlock = className?.startsWith('language-')
    if (isBlock) {
      return (
        <Box
          as="pre"
          bg="bg.muted"
          p={3}
          borderRadius="md"
          overflowX="auto"
          fontFamily="mono"
          fontSize="xs"
          my={2}
        >
          <code>{children}</code>
        </Box>
      )
    }
    return (
      <Code bg="bg.muted" px={1} borderRadius="sm" fontFamily="mono" fontSize="xs">
        {children}
      </Code>
    )
  },
  pre: ({ children }) => <>{children}</>,
  h1: ({ children }) => (
    <Text fontWeight="bold" fontSize="md" mt={3} mb={1}>
      {children}
    </Text>
  ),
  h2: ({ children }) => (
    <Text fontWeight="bold" fontSize="sm" mt={3} mb={1}>
      {children}
    </Text>
  ),
  h3: ({ children }) => (
    <Text fontWeight="semibold" fontSize="sm" mt={2} mb={1}>
      {children}
    </Text>
  ),
  table: ({ children }) => (
    <Box overflowX="auto" my={2}>
      <Table size="sm" variant="simple">
        {children}
      </Table>
    </Box>
  ),
  thead: ({ children }) => <Thead>{children}</Thead>,
  tbody: ({ children }) => <Tbody>{children}</Tbody>,
  tr: ({ children }) => <Tr>{children}</Tr>,
  th: ({ children }) => (
    <Th fontSize="xs" color="text.secondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
      {children}
    </Th>
  ),
  td: ({ children }) => (
    <Td fontSize="xs" sx={{ fontVariantNumeric: 'tabular-nums' }}>
      {children}
    </Td>
  ),
  blockquote: ({ children }) => (
    <Box borderLeft="3px solid" borderColor="brand.primary" pl={3} my={2} color="text.secondary">
      {children}
    </Box>
  ),
  hr: () => <Divider my={3} borderColor="bg.panel" />,
}

interface MarkdownContentProps {
  content: string
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <Box sx={{ '& > *:last-child': { mb: 0 } }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </Box>
  )
}
