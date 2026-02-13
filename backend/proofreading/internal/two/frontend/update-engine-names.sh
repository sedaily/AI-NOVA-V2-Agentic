#!/bin/bash

echo "Updating engine names from T5/H8 to Basic/Pro..."

# Find and replace T5 with Basic and H8 with Pro in all JS/JSX files
find src -type f \( -name "*.js" -o -name "*.jsx" \) -exec sed -i '' \
  -e 's/"T5"/"Basic"/g' \
  -e "s/'T5'/'Basic'/g" \
  -e 's/"H8"/"Pro"/g' \
  -e "s/'H8'/'Pro'/g" \
  -e 's/T5NH8/BasicNPro/g' \
  -e 's/T5 엔진/Basic 엔진/g' \
  -e 's/H8 엔진/Pro 엔진/g' \
  -e 's/t5/basic/g' \
  -e 's/h8/pro/g' \
  {} +

echo "Update complete!"