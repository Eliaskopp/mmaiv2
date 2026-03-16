import { Button, SimpleGrid } from '@chakra-ui/react'

interface ChoiceChipGroupProps {
  options: { value: string; label: string }[]
  value: string | null
  onChange: (value: string) => void
  columns?: number
}

export function ChoiceChipGroup({ options, value, onChange, columns = 2 }: ChoiceChipGroupProps) {
  return (
    <SimpleGrid columns={columns} spacing={2}>
      {options.map((opt) => {
        const isSelected = opt.value === value
        return (
          <Button
            key={opt.value}
            variant={isSelected ? 'solid' : 'outline'}
            bg={isSelected ? 'brand.primary' : 'bg.muted'}
            color={isSelected ? 'white' : 'text.primary'}
            borderColor="transparent"
            _hover={{
              bg: isSelected ? 'brand.600' : 'bg.panel',
            }}
            onClick={() => onChange(opt.value)}
            size="sm"
            minH="48px"
          >
            {opt.label}
          </Button>
        )
      })}
    </SimpleGrid>
  )
}
