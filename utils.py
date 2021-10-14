import pandas as pd
import numpy as np
import json



class Ingredients():
    
    def __init__(self, json_path):
        with open(json_path) as json_file:
            self.ingredient_scores_dict = json.load(json_file)
        
    def add_ing_categories(self, csv_path):
    # pip3 install openpyxl to be able to execute this code.
        df = pd.read_csv(csv_path, index_col='slider')
        df.fillna(0, inplace=True)
        self.ing_df = df
    
    def add_slider(self, slider_path):
        with open(slider_path, 'r') as slider_file:
            slider_text = slider_file.read()
            self.slider = json.loads(slider_text)
            self.wrong_ingredients()

    def wrong_ingredients(self):
        l = list()
        for _type in self.slider.keys():
            if self.slider[_type]:
                ser = self.ing_df[_type]
                l += list((ser[ser == 0]).index)
        self.wrong_ing_set = set(l)
    
    def add_dish_df(self, dish_df_obj):
        self.ddf = dish_df_obj
        self.filter_dishes()  

    def filter_dishes(self):
        '''
        Transforms ddf based on filters.
        '''
        ddf = self.ddf
        ser_fil = pd.Series(True, ddf.index)
        for ing in ddf.columns:
            if ing in self.wrong_ing_set:
                ser_fil = ser_fil & (ddf[ing] == 0)
        self.ddf = DishTypeDataFrame(ddf[ser_fil])

    def calculate_dish_scores_as_dict(self):
        self.dish_scores = {}
        kisi_ort_dict = self.ddf['kisi_ort'].to_dict()
        dish_and_ingr_binary_dict = self.ddf.show_dishes_and_ingredients_01_as_dict()
        for dish in self.ddf.index:
            dish_total = 0
            for ingredient in dish_and_ingr_binary_dict[dish].keys():
                try:
                    value = dish_and_ingr_binary_dict[dish][ingredient] * self.ingredient_scores_dict[ingredient]
                except KeyError: # If the ingredient does not exist in the ingredient_scores_2174 (a.k.a. 'food_scores_2174.json')
                    value = 0
                dish_total += value
            self.dish_scores[dish] = np.round(dish_total / kisi_ort_dict[dish], 2)

    def ddf_with_scores(self):
        self.calculate_dish_scores_as_dict()
        ddf_to_write = self.ddf.copy(deep=True)
        ddf_to_write['Scores'] = pd.Series(self.dish_scores)
        ddf_to_write.sort_values(by=['Scores'], axis=0, inplace=True, ascending=False)
        return ddf_to_write
    
    def prepare_ddf_to_write(self):
        ddf_to_write = self.ddf_with_scores()
        cols = list(ddf_to_write.columns)
        cols = cols[-1:] + cols[:-1]
        cols_to_del = ['kişi', 'kisi1', 'kisi2', 'kisi_ort', 'tarif']
        for colname in cols_to_del:
            cols.remove(colname)
        ddf_to_write = ddf_to_write[cols]
        return ddf_to_write

    def write_ddf_to_excel(self, excel_writer_obj, sheet):
        ddf_to_write = self.prepare_ddf_to_write()
        ddf_to_write.to_excel(excel_writer_obj, sheet_name=sheet)
    
    def return_dict(self):
        ddf_to_use = self.prepare_ddf_to_write()
        dct = ddf_to_use.T.to_dict()
        return dct



class DishTypeDataFrame(pd.DataFrame):
    ''' 
    This class represents one sheet 
    or equivalently one dish type in the .xlsx file.
    '''
    def show_recipes_as_dict(self):
        return self['tarif'].to_dict()
    
    def dishes_and_ingredients_gr_as_df(self):
        cols_to_use = list(self.columns)
        cols_to_del = ['tarif', 'kişi']
        for colname in cols_to_del:
            cols_to_use.remove(colname)
        ddf = self[cols_to_use]
        ddf = ddf.astype(float, errors='ignore')
        return ddf

    def show_dishes_and_ingredients_gr_as_dict(self):
        ddf = self.dishes_and_ingredients_gr_as_df()
        dictionary = ddf.T.to_dict()
        return dictionary
        
    def show_dishes_and_ingredients_01_as_dict(self):
        ddf = self.dishes_and_ingredients_gr_as_df()
        ddf = (ddf > 0) * 1
        dictionary = ddf.T.to_dict()
        return dictionary



class AllDishes():
    '''
    This class represents all dish types and the corresponding dishes. 
    In other words, it represents the whole .xlsx file.
    '''
    def __init__(self, xlsx_path):
        # pip3 install openpyxl to be able to execute this code.
        self.all_sheets_raw_dict = pd.read_excel(xlsx_path, engine='openpyxl', sheet_name=None)
        self._sheet_names()
        self._sheet_iterate()

    def _sheet_names(self):
        sheet_names = list(self.all_sheets_raw_dict.keys())
        self.sheet_names = sheet_names[:-1] # Do not include the empty sheet called 'Sayfa1' in the xlsx file.
    
    def _sheet_iterate(self):
        self.all_sheets_preprocessed_dict = dict()
        for sheet_name in self.sheet_names:
            self.all_sheets_preprocessed_dict[sheet_name] = self._sheet_preprocessor(sheet_name)

    def _sheet_preprocessor(self, sheet_name):
        ddf = DishTypeDataFrame(self.all_sheets_raw_dict[sheet_name])
        ddf.drop_duplicates(['YEMEK ADI'], inplace=True)
        ddf['YEMEK ADI'] = ddf['YEMEK ADI'].astype(str)
        ddf.index = ddf['YEMEK ADI']
        ddf.dropna(inplace=True)
        ddf.drop('YEMEK ADI', axis=1, inplace=True)
        ddf['kisi1'] = ddf['kişi'].str.extract('(\d)').astype(float)
        ddf['kisi2'] = ddf['kişi'].str.extract('(\d)-(\d)')[1].astype(float)
        ddf['kisi_ort'] = ddf[['kisi1', 'kisi2']].mean(skipna=True, axis=1)
        return ddf
    
    def get_sheet(self, sheet_name):
        return self.all_sheets_preprocessed_dict[sheet_name]
