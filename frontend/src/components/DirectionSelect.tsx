import { useAppStore } from '@/store/useAppStore'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'

export function DirectionSelect() {
  const direction = useAppStore((state) => state.direction)
  const setDirection = useAppStore((state) => state.setDirection)

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="direction-select" className="text-sm font-medium">
        Dirección:
      </Label>
      <Select value={direction} onValueChange={setDirection}>
        <SelectTrigger id="direction-select" className="w-[220px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="es-da">
            <span className="flex items-center gap-2">
              🇪🇸 Español → 🇩🇰 Danés
            </span>
          </SelectItem>
          <SelectItem value="da-es">
            <span className="flex items-center gap-2">
              🇩🇰 Danés → 🇪🇸 Español
            </span>
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}

