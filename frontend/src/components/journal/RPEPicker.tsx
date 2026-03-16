import { Box, SimpleGrid, Text } from '@chakra-ui/react'
import { getRPEColor, getRPELabel } from './session-utils'

interface RPEPickerProps {
  value: number | null
  onChange: (value: number | null) => void
}

export function RPEPicker({ value, onChange }: RPEPickerProps) {
  return (
    <Box>
      <SimpleGrid columns={5} spacing={2}>
        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => {
          const isSelected = value === n
          return (
            <Box
              key={n}
              w="40px"
              h="40px"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              mx="auto"
              cursor="pointer"
              fontWeight="semibold"
              fontSize="sm"
              bg={isSelected ? getRPEColor(n) : 'bg.muted'}
              color={isSelected ? 'white' : 'text.secondary'}
              transform={isSelected ? 'scale(1.1)' : 'scale(1)'}
              transition="all 0.15s ease"
              onClick={() => onChange(value === n ? null : n)}
              _hover={{ bg: isSelected ? getRPEColor(n) : 'bg.panel' }}
            >
              {n}
            </Box>
          )
        })}
      </SimpleGrid>
      <Text fontSize="xs" color="text.muted" mt={2} textAlign="center" h="16px">
        {value ? getRPELabel(value) : ''}
      </Text>
    </Box>
  )
}
