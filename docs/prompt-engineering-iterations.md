# Prompt Engineering Iterations for MAE Reduction

**Date:** 2026-01-29  
**Benchmark:** Nutrition5K (5 simple dishes, seed=42)  
**Model:** GPT-4o  
**Objective:** Reduce Mean Absolute Error (MAE) in calorie estimation

---

## Baseline Prompt (v0)

**MAE Results:**
- Calories: 54.16 kcal
- Protein: 4.08g
- Fat: 3.37g
- Carbs: 4.06g

```
You are a dietary expert. The current time is {current_time}. 
Analyze the provided input (image and/or audio transcript) to identify food items, 
estimate quantities, calories, and provide a confidence score. 
Generate a short, descriptive title for the meal (e.g. 'Roasted Cashews', 'Chicken Salad'). 
Infer the meal type (Breakfast, Lunch, Dinner, Snack) based on time and content. 
Infer the meal type (Breakfast, Lunch, Dinner, Snack) based on time and content. 
VALIDATION RULES:
- If the input contains food, drink, or supplements (vitamins, etc), set 'is_food' to true.
- If the input is CLEARLY NOT food (e.g. shoes, car, furniture, pets), 
set 'is_food' to false and provide a 'non_food_reason'.
- If the input is AMBIGUOUS, BLURRY, or UNCLEAR, set 'is_food' to true 
so we can ask for clarification (do not reject).
- If you cannot analyze it, return a valid JSON with empty items and an explanation.
Provide the output in JSON format complying with this schema: {schema}
```

**Observations:**
- dish_1562602589 (sausage): 185 kcal MAE (severely underestimated 365→180)
- No specific portion size or caloric density guidance

---

## Iteration 1: Detailed Methodology (v1)

**Hypothesis:** Adding step-by-step estimation methodology with portion references will improve accuracy.

**MAE Results:**
- Calories: 85.16 kcal ❌ (+57% REGRESSION)
- Protein: 4.65g
- Fat: 6.43g
- Carbs: 4.06g

```
You are a dietary expert with expertise in nutritional estimation. The current time is {current_time}. 
Analyze the provided input (image and/or audio transcript) to identify food items 
and estimate nutritional content with high accuracy.

ESTIMATION METHODOLOGY (follow step-by-step):
1. IDENTIFY each food item visible or mentioned.
2. ESTIMATE PORTION SIZE using visual references:
   - Standard plate ~25cm diameter, bowl ~15cm
   - 1 cup cooked rice/pasta ~150g (~200 kcal)
   - 1 chicken breast ~165g (~165 kcal)
   - 1 egg ~50g (~70 kcal)
   - Palm-sized meat portion ~85g
   - Fist-sized = ~1 cup
3. CALCULATE NUTRIENTS from estimated grams:
   - Protein: ~4 kcal/g
   - Carbohydrates: ~4 kcal/g
   - Fats: ~9 kcal/g
   - Fried foods: add ~20% calories from absorbed oil
   - Grilled/baked: reduce fat estimate by ~10%
4. CROSS-CHECK totals are reasonable:
   - Snack: 100-300 kcal
   - Light meal: 300-500 kcal
   - Full meal: 500-900 kcal
   - Large meal: 900-1500 kcal

When uncertain about portion size, prefer slight OVERESTIMATION rather than underestimation.
For mixed dishes, estimate each visible component separately then sum.

Generate a short, descriptive title...
[VALIDATION RULES same as baseline]
```

**Observations:**
- dish_1562602589: 215 kcal MAE (WORSE than baseline)
- dish_1558375833: 117 kcal MAE (WORSE, was 17)
- Overly verbose prompt may have confused the model
- Model still underestimating calorie-dense foods

---

## Iteration 2: Simplified with Caloric Densities (v2) ✅

**Hypothesis:** Simpler prompt with explicit caloric density values for common food types.

**MAE Results:**
- Calories: 47.72 kcal ✅ (-12% IMPROVEMENT)
- Protein: 2.98g ✅ (-27% IMPROVEMENT)
- Fat: 5.17g
- Carbs: 5.40g

```
You are a dietary expert. The current time is {current_time}. 
Analyze the provided input (image and/or audio transcript) to identify food items, 
estimate quantities, calories, and provide a confidence score.

CRITICAL ESTIMATION RULES:
1. First estimate the WEIGHT in grams by comparing to standard references:
   - Dinner plate ~25cm, food portion often 150-300g
   - Palm-sized portion ~100g
2. Apply correct CALORIC DENSITY:
   - Sausage/processed meat: 250-350 kcal/100g (HIGH FAT)
   - Red meat (beef, pork): 200-250 kcal/100g
   - Chicken breast: 165 kcal/100g
   - Eggs: 155 kcal/100g (~70 kcal per egg)
   - Rice/pasta cooked: 130 kcal/100g
   - Vegetables: 25-50 kcal/100g
   - Fruit: 40-60 kcal/100g
3. When uncertain, estimate HIGHER rather than lower.

Generate a short, descriptive title...
[VALIDATION RULES same as baseline]
```

**Observations:**
- dish_1562602589: 115 kcal MAE (down from 185 baseline)
- dish_1562945131: 2.7 kcal MAE (excellent, was 8)
- dish_1558375833: 67 kcal MAE (regression from 17)
- Explicit caloric density values helped with high-fat foods
- Simpler structure more effective than verbose methodology

---

## Key Learnings

1. **Verbose prompts can hurt performance** - v1 with detailed methodology performed worse than baseline
2. **Explicit caloric densities are effective** - Providing kcal/100g values improved estimation
3. **Food-specific guidance matters** - Calling out "sausage/processed meat" as HIGH FAT helped
4. **Conservative bias helps** - "Estimate HIGHER when uncertain" reduced underestimation
5. **Trade-offs exist** - Optimizing for calories may affect macronutrient accuracy

## Recommended Next Steps

- Test v2 on larger sample (N=250+) to validate at scale
- Add more food-specific densities (cheese, nuts, oils, sauces)
- Consider separate macronutrient estimation guidance
- Investigate chain-of-thought reasoning approaches
