import os

class read_configmap:

    def __init__ (self, __config_path):
        self.config_path = __config_path
    
    def list_files(self):
        all_files = os.listdir(self.config_path)

        files = []

        for file in all_files:
            if (file[0:2] != ".."):
                files.append(file)
        
        return files

    def read_files(self, files):

        configs = {}
        for file_name in files:
            data = open(f"{self.config_path}/{file_name}").read().strip("\n").replace('"', '').split("\n")

            configs[file_name] = {}
            
            for item in data:
                if ("=" in item):
                    item = item.split("=")
                    configs[file_name][item[0]] = item[1]
                
                else:
                    configs[file_name] = data[0]
        
        return configs
    
    def main(self):
        files = self.list_files()
        configs = self.read_files(files)
 
        return configs