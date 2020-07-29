
# Copyright (c) 2019, Build-A-Cell. All rights reserved.
# See LICENSE file in the project root directory for details.

from warnings import warn
from warnings import resetwarnings
from .parameter import ParameterDatabase
from .component import Component
from .chemical_reaction_network import ChemicalReactionNetwork
from .species import Species
from .reaction import Reaction
from .mechanism import Mechanism
from .global_mechanism import GlobalMechanism
import copy
from typing import List, Union


class Mixture(object):
    def __init__(self, name="", mechanisms=None, components=None, parameters=None, parameter_file=None,
        global_mechanisms=None, species=None, initial_condition_dictionary=None, **kwargs):
        """
        A Mixture object holds together all the components (DNA,Protein, etc), mechanisms (Transcription, Translation),
        and parameters related to the mixture itself (e.g. Transcription rate). Default components and mechanisms can be
        added as well as global mechanisms that impacts all species (e.g. cell growth).

        :param name: Name of the mixture
        :param mechanisms: Dictionary of mechanisms
        :param components: List of components in the mixture (list of Components)
        :param parameters: Dictionary of parameters (check parameters documentation for the keys)
        :param parameter_file: Parameters can be loaded from a parameter file
        :param default_mechanisms:
        :param global_mechanisms: dict of global mechanisms that impacts all species (e.g. cell growth)
        """
        # Initialize instance variables
        self.name = name  # Save the name of the mixture

        # process the components
        if components is None and not hasattr(self, "_components"):
            self.components = []
        else:
            self.add_components(components)

        #process mechanisms:
        if mechanisms is None and not hasattr(self, "_mechanisms"):
            self.mechanisms = {}
        else:
            self.add_mechanisms(mechanisms)

        #process global_mechanisms:

        # Global mechanisms are applied just once ALL species generated from
        # components inside a mixture
        # Global mechanisms should be used rarely, and with care. An example
        # usecase is degradation via dilution.
        if global_mechanisms is None and not hasattr(self, "_global_mechanisms"):
            self.global_mechanisms = {}
        else:
            self.add_mechanisms(global_mechanisms)

        # process the species
        self.add_species(species)

        #Create a paraemter database
        self.parameter_database = ParameterDatabase(parameter_file = parameter_file, parameter_dictionary = parameters, **kwargs)
        
        # Initial conditions are searched for by defauled in the parameter file
        # see Mixture.set_initial_condition(self)
        # These can be overloaded with custom_initial_condition dictionary: component.name --> initial amount
        if initial_condition_dictionary is None:
            self.initial_condition_dictionary = {}
        else:
            self.initial_condition_dictionary = dict(initial_condition_dictionary)


        # internal lists for the species and reactions
        self.crn_species = None
        self.crn_reactions = None

    def add_species(self, species: Union[List[Species], Species]):
        if not hasattr(self, "added_species"):
            self.added_species = []

        if species is not None:
            if not isinstance(species, list):
                species_list = [species]
            else:
                species_list = species

            assert all(isinstance(x, Species) for x in species_list), 'only Species type is accepted!'

            self.added_species += species_list


    #Used to set internal species froms strings, Species or Components
    def set_species(self, species, material_type = None, attributes = None):
        if isinstance(species, Species):
            return species
        elif isinstance(species, str):
            return Species(name = species, material_type = material_type, attributes = attributes)
        elif isinstance(species, Component) and species.get_species() is not None:
            return species.get_species()
        else:
            raise ValueError("Invalid Species: string, chemical_reaction_network.Species or Component with implemented .get_species() required as input.")


    @property
    def components(self):
        return self._components
    @components.setter
    def components(self, components):
        self._components = []
        self.add_components(components)
    
    def add_component(self, component):
        """
        this function adds a single component to the mixture
        """
        if not hasattr(self, "_components"):
            self.components = []

        if isinstance(component, list):
            self.add_components(component)
        else:
            assert isinstance(component, Component), "the object: %s passed into mixture as component must be of the class Component" % str(component)

            #Check if component is already in self._components
            for comp in self._components:
                if type(comp) == type(component) and comp.name == component.name:
                    raise ValueError(f"{comp} of the same type and name already in Mixture!")
            else:
                #Components are copied before being added to Mixtures
                component_copy = copy.deepcopy(component)
                component_copy.set_mixture(self)
                self.components.append(component_copy)


    def add_components(self, components: Union[List[Component], Component]):
        """
        This function adds a list of components to the mixture
        """
        if isinstance(components, Component):
            self.add_component(components)
        elif isinstance(components, List):
            for component in components:
                self.add_component(component)
        else:
            raise ValueError(f"add_components expected a list of Components. Recieved {components}")

    def get_component(self, component = None, name = None, index = None):
        """
        Function to get components from Mixture._components.

        One of the 3 keywords must not be None.

        component: an instance of a component. Searches Mixture._components for a Component with the same type and name.
        name: str. Searches Mixture._components for a Component with the same name
        index: int. returns Mixture._components[index]

        if nothing is found, returns None.
        """

        if [component, name, index].count(None) != 2:
            raise ValueError(f"get_component requires a single keyword. Recieved component={component}, name={name}, index={index}.")
        if not (isinstance(component, Component) or component is None):
            raise ValueError(f"component must be of type Component. Recieved {component}.")
        if not (isinstance(name, str) or name is None):
            raise ValueError(f"name must be of type str. Recieved {name}.")
        if not (isinstance(index, int) or index is None):
            raise ValueError(f"index must be of type int. Recieved {index}.")

        matches = []
        if index is not None:
            matches.append(self.components[index])
        else:
            for comp in self.components:
                if component is not None:
                    if type(comp) == type(component) and comp.name == component.name:
                        matches.append(comp)
                elif name is not None:
                    if comp.name == name:
                        matches.append(comp)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            warn("get_component found multiple matching components. A list has been returned.")
            return matches 

    @property
    def mechanisms(self):
        """
        mechanisms stores Mixture Mechanisms
        """
        return self._mechanisms

    @mechanisms.setter
    def mechanisms(self, mechanisms):
        self._mechanisms = {}
        self.add_mechanisms(mechanisms, overwrite = True)
        
    def add_mechanism(self, mechanism, mech_type = None, overwrite = False):
        """
        adds a mechanism of type mech_type to the Mixture mechanism_dictonary.
        keywordS:
          mechanism: a Mechanism instance
          mech_type: the type of mechanism. defaults to mechanism.mech_type if None
          overwrite: whether to overwrite existing mechanisms of the same type (default False)

        """
        if not hasattr(self, "_mechanisms"):
            self._mechanisms = {}

        if not isinstance(mechanism, Mechanism):
            raise TypeError(f"mechanism must be a Mechanism. Recieved {mechanism}.")

        if mech_type is None:
            mech_type = mechanism.mechanism_type
        if not isinstance(mech_type, str):
            raise TypeError(f"mechanism keys must be strings. Recieved {mech_type}")

        if isinstance(mechanism, GlobalMechanism):
            self.add_global_mechanism(mechanism, mech_type, overwrite)
        elif isinstance(mechanism, Mechanism):
            if mech_type in self._mechanisms and not overwrite:
                raise ValueError(f"mech_type {mech_type} already in Mixture {self}. To overwrite, use keyword overwrite = True.")
            else:
                self._mechanisms[mech_type] = copy.deepcopy(mechanism)
        
    def add_mechanisms(self, mechanisms, overwrite = False):
        """
        This function adds a list or dictionary of mechanisms to the mixture. Can take both GlobalMechanisms and Mechanisms
        """
        if isinstance(mechanisms, Mechanism):
            self.add_mechanism(mechanisms, overwrite = overwrite)
        elif isinstance(mechanisms, dict):
            for mech_type in mechanisms:
                self.add_mechanism(mechanisms[mech_type], mech_type, overwrite = overwrite)
        elif isinstance(mechanisms, list):
            for mech in mechanisms:
                self.add_mechanism(mech, overwrite = overwrite)
        else:
            raise ValueError(f"add_mechanisms expected a list of Mechanisms. Recieved {mechanisms}")


    def get_mechanism(self, mechanism_type):
        """
        Searches the Mixture for a Mechanism of the correct type. 
        If no Mechanism is found, None is returned.
        """
        if not isinstance(mechanism_type, str):
            raise TypeError(f"mechanism_type must be a string. Recievied {mechanism_type}.")

        if mechanism_type in self.mechanisms:
            return self.mechanisms[mechanism_type]
        else:
            return None
                
    @property
    def global_mechanisms(self):
        """
        global_mechanisms stores global Mechanisms in the Mixture
        """
        return self._global_mechanisms

    @global_mechanisms.setter
    def global_mechanisms(self, mechanisms):
        self._global_mechanisms = {}
        if isinstance(mechanisms, dict):
            for mech_type in mechanisms:
                self.add_global_mechanism(mechanisms[mech_type], mech_type, overwrite = True)
        elif isinstance(mechanisms, list):
            for mech in mechanisms:
                self.add_global_mechanism(mech, overwrite = True)

    def add_global_mechanism(self, mechanism, mech_type = None, overwrite = False):
        """
        adds a mechanism of type mech_type to the Mixture global_mechanism dictonary.
        keywordS:
          mechanism: a Mechanism instance
          mech_type: the type of mechanism. defaults to mechanism.mech_type if None
          overwrite: whether to overwrite existing mechanisms of the same type (default False)
        """
        if not hasattr(self, "_global_mechanisms"):
            self._global_mechanisms = {}

        if not isinstance(mechanism, GlobalMechanism):
            raise TypeError(f"mechanism must be a GlobalMechanism. Recieved {mechanism}.")

        if mech_type is None:
            mech_type = mechanism.mechanism_type
        if not isinstance(mech_type, str):
            raise TypeError(f"mechanism keys must be strings. Recieved {mech_type}")

        if mech_type in self._mechanisms and not overwrite:
            raise ValueError(f"mech_type {mech_type} already in Mixture {self}. To overwrite, use keyword overwrite = True.")
        else:
            self._global_mechanisms[mech_type] = copy.deepcopy(mechanism)

    def update_parameters(self, parameter_file = None, parameters = None, overwrite_parameters = True):
        if parameter_file is not None:
            self.parameter_database.load_parameters_from_file(parameter_file, overwrite_parameters = overwrite_parameters)

        if parameters is not None:
            self.parameter_database.load_parameters_from_dictionary(parameters, overwrite_parameters = overwrite_parameters)
    
    def get_parameter(self, mechanism, part_id, param_name):
        param = self.parameter_database.find_parameter(mechanism, part_id, param_name)

        return param
    
    #Tries to find an initial condition of species s using the parameter heirarchy
    # 1. Tries to find the initial concentration in the Component initial_Concentration_dictionary and ParameterDatabase
    # 2. Tries to find self.name, repr(s) in self.initial_condition_dictionary
    # 3. Tries to find repr(s) in self.initial_condition_dictionary
    # 4. if s == component.get_species(), tries to find (None, self.name, component.name) in self.initial_condition_dictionary
    # 5. if s == component.get_species(), tries to find component.name in self.initial_condition_dictionary
    # 6. tries to find (None, self.name, repr(s)) in self.parameter_database
    # 7. tries to find repr(s) in self.parameter_database
    # 8. if s == component.get_species(), tries to find (None, self.name, component.name) in self.parameter_database
    # 9. if s == component.get_species(), tries to find component.name in self.parameter_database
    # 10-. defaults to 0
    def set_initial_condition(self, s, component = None):
        if not isinstance(s, Species):
            raise ValueError(f"{s} is not a Species! Can only set initial concentration of a Species.")

        init_conc = None
        #1
        if component is not None:
            init_conc = component.get_initial_condition(s)

        if init_conc is None:
            #2
            if (self.name, repr(s)) in self.initial_condition_dictionary:
                init_conc = self.initial_condition_dictionary[(self.name, repr(s))]
            #3
            elif repr(s) in self.initial_condition_dictionary:
                init_conc = self.initial_condition_dictionary[repr(s)]
            #4
            elif component is not None and component.get_species() == s and (self.name, component.name) in self.initial_condition_dictionary:
                return self.initial_condition_dictionary[(self.name, component.name)]
            #5
            elif component is not None and component.get_species() == s and component.name in self.initial_condition_dictionary:
                return self.initial_condition_dictionary[component.name]
            #6
            elif self.parameter_database.find_parameter(None, self.name, repr(s)) is not None:
                init_conc = self.parameter_database.find_parameter(None, self.name, repr(s)).value
            #7
            elif self.parameter_database.find_parameter(None, None, repr(s)) is not None:
                init_conc = self.parameter_database.find_parameter(None, None, repr(s)).value
            #8
            elif component is not None and component.get_species() == s and (None, self.name, component.name) in self.parameter_database:
                return self.parameter_database.find_parameter(None, self.name, component.name).value
            #9
            elif component is not None and component.get_species() == s and component.name in self.parameter_database:
                return self.parameter_database.find_parameter(None, None, component.name).value
            #10
            else:
                init_conc = 0

        s.initial_concentration = init_conc


    #Allows mechanisms to return nested lists of species. These lists are flattened.
    def append_species(self, new_species, component):
        for s in new_species:
            if isinstance(s, Species):
                self.set_initial_condition(s, component)
                self.crn_species.append(s)
            elif isinstance(s, list) and(all(isinstance(ss, Species) for ss in s) or len(s) == 0):
                for ss in s: 
                    self.set_initial_condition(ss, component)
                self.crn_species+=s
            elif s is not None:
                raise ValueError(f"Invalid Species Returned in {component}.update_species(): {s}.")
        #Old Version
        #self.crn_species += [s for s in new_species if s not in self.crn_species]


    def update_species(self) -> List[Species]:
        """ it generates the list of species based on all the mechanisms in each Component
        :return: list of species generated by all the mechanisms and global mechanisms
        """
        self.crn_species = []
        #Append Species added manually
        self.append_species(self.added_species, None)

        #Appendy species from each Component
        for component in self.components:
            self.append_species(component.update_species(), component)

        return self.crn_species

    def update_reactions(self) -> List[Reaction]:
        """ it generates the list of reactions based on all the mechanisms and global mechanisms
        it **must be** called after update_species() was called!

        :raise: AttributeError if it was called before update_species()
        :return: list of reactions generated by all the mechanisms and global mechanisms
        """
        if self.crn_species is None:
            raise AttributeError("Mixture.crn_species not defined. "
                                 "mixture.update_species() must be called "
                                 "before mixture.update_reactions()")

        self.crn_reactions = []
        for component in self.components:
            self.crn_reactions += component.update_reactions()

        return self.crn_reactions

        
    def apply_global_mechanisms(self) -> (List[Species], List[Reaction]):
        # update with global mechanisms

        if self.crn_species is None:
            raise AttributeError("Mixture.crn_species not defined. "
                                 "mixture.update_species() must be called "
                                 "before mixture.apply_global_mechanisms()")
        global_mech_species = []
        global_mech_reactions = []
        if self.global_mechanisms:
            for mech in self.global_mechanisms:
                # Update Global Mechanisms
                global_mech_species += self.global_mechanisms[mech].update_species_global(self.crn_species, self)
                global_mech_reactions += self.global_mechanisms[mech].update_reactions_global(self.crn_species, self)

        return global_mech_species, global_mech_reactions

    def compile_crn(self) -> ChemicalReactionNetwork:
        """ Creates a chemical reaction network from the species and reactions associated with a mixture object
        :return: ChemicalReactionNetwork
        """
        resetwarnings()#Reset warnings - better to toggle them off manually.

        #reset the Components' mixture to self - in case they have been added to other Mixtures
        for c in self.components:
            c.set_mixture(self)

        self.update_species() #updates species to self.crn_species and sets initial concentrations
        self.update_reactions() #updates reactions to self.crn_reactions

        #global mechanisms are applied last and only to all the species 
        global_mech_species, global_mech_reactions = self.apply_global_mechanisms()

        #append global species to self.crn_species and update initial concentrations
        if isinstance(global_mech_species, list) and len(global_mech_species) > 0:
            self.append_species(global_mech_species, component = None)

        #append global reactions
        if isinstance(global_mech_reactions, list) and len(global_mech_reactions)>0:
            self.crn_reactions += global_mech_reactions 

        CRN = ChemicalReactionNetwork(list(self.crn_species), list(self.crn_reactions))
        return CRN

    def __str__(self):
        return type(self).__name__ + ': ' + self.name

    def __repr__(self):
        txt = str(self)+"\n"
        if self.components:
            txt += "Components = ["
            for comp in self.components:
                txt+="\n\t"+str(comp)
        if self.mechanisms:
            txt+=" ]\nMechanisms = {"
            for mech in self.mechanisms:
                txt+="\n\t"+mech+":"+self.mechanisms[mech].name
        if self.global_mechanisms:
            txt+=" }\nGlobal Mechanisms = {"
            for mech in self.global_mechanisms:
                txt+="\n\t"+mech+":"+self.global_mechanisms[mech].name
        txt+=" }"
        return txt




