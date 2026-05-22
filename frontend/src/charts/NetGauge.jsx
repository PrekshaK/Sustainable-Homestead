import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const W = 160, H = 100
const CX = W / 2, CY = H - 5
const R_OUT = 72, R_IN = 50
const MIN = -60, MAX = 60

export function NetGauge({ net }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return
    const svg = d3.select(ref.current)
    svg.selectAll('*').remove()

    const pct = Math.max(0, Math.min(1, (net - MIN) / (MAX - MIN)))
    const color = net >= 1 ? '#22c55e' : net <= -1 ? '#ef4444' : '#eab308'
    const arc = d3.arc().innerRadius(R_IN).outerRadius(R_OUT)
    const g = svg.append('g').attr('transform', `translate(${CX},${CY})`)

    // Background track
    g.append('path')
      .attr('d', arc({ startAngle: -Math.PI / 2, endAngle: Math.PI / 2 }))
      .attr('fill', '#1f2937')

    // Value fill
    g.append('path')
      .attr('d', arc({ startAngle: -Math.PI / 2, endAngle: -Math.PI / 2 + pct * Math.PI }))
      .attr('fill', color)
      .attr('opacity', 0.9)

    // Zero tick
    g.append('line')
      .attr('x1', 0).attr('y1', -(R_IN + 1))
      .attr('x2', 0).attr('y2', -(R_OUT + 5))
      .attr('stroke', '#6b7280').attr('stroke-width', 1.5)

    // Value label
    g.append('text')
      .attr('text-anchor', 'middle').attr('y', -18)
      .attr('fill', color)
      .attr('font-size', 22).attr('font-weight', '700')
      .attr('font-family', 'ui-monospace, monospace')
      .text(net > 0 ? `+${net.toFixed(1)}` : net.toFixed(1))

    g.append('text')
      .attr('text-anchor', 'middle').attr('y', -3)
      .attr('fill', '#6b7280').attr('font-size', 10)
      .text('net kWh')

    // Range labels
    g.append('text').attr('x', -(R_OUT + 4)).attr('y', 5)
      .attr('text-anchor', 'end').attr('fill', '#4b5563').attr('font-size', 9).text(MIN)
    g.append('text').attr('x', R_OUT + 4).attr('y', 5)
      .attr('text-anchor', 'start').attr('fill', '#4b5563').attr('font-size', 9).text(`+${MAX}`)

  }, [net])

  return <svg ref={ref} width={W} height={H} />
}
