

class read_configmap:

    def __init__ (self, __config_path, __file_names):
        self.config_path = __config_path
        self.file_names = __file_names

    def read_files(self):

        configs = {}
        for file_name in self.file_names:
            data = open(f"{self.config_path}/{file_name}").read().strip("\n").replace('"', '').split("\n")

            configs[file_name] = {}
            
            for item in data:
                    configs[file_name] = data
        
        return configs
    
    def main(self):
        configs = self.read_files()
 
        return configs