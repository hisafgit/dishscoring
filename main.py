from utils import *

xlsx_file_name = 'sample_other_dishes.xlsx'
json_file_name = 'sample_food_scores.json'

dsh = AllDishes(xlsx_path = xlsx_file_name)
ings = Ingredients(json_path = json_file_name)
ings.add_ing_categories('sample_ingredient_filter.csv')
ings.add_slider('sample_filter_slider.json')

d = {}
for sheet in dsh.sheet_names:
    ddf = dsh.get_sheet(sheet)
    ings.add_dish_df(ddf)
    d[sheet] = ings.return_dict()

with open("out.json", "w") as f:
    json.dump(d, f)
