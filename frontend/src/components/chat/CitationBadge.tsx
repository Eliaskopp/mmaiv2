import { Tag, TagLabel, TagLeftIcon } from '@chakra-ui/react'
import { Dumbbell, Globe, Heart, StickyNote } from 'lucide-react'

export interface Citation {
  id: string
  type: 'web' | 'session' | 'note' | 'recovery'
  title: string
  url?: string
  source_id?: string
  snippet?: string
}

const TYPE_ICONS: Record<Citation['type'], React.ElementType> = {
  web: Globe,
  session: Dumbbell,
  note: StickyNote,
  recovery: Heart,
}

interface CitationBadgeProps {
  citation: Citation
  onClick: (citation: Citation) => void
}

export function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  const Icon = TYPE_ICONS[citation.type] || Globe

  return (
    <Tag
      size="sm"
      bg="bg.muted"
      color="text.secondary"
      borderRadius="full"
      cursor="pointer"
      _hover={{ bg: 'bg.panel' }}
      transition="background 0.15s"
      onClick={() => onClick(citation)}
    >
      <TagLeftIcon as={Icon} boxSize="12px" />
      <TagLabel maxW="120px" isTruncated fontSize="2xs">
        {citation.title}
      </TagLabel>
    </Tag>
  )
}
