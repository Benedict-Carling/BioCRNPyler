from .mechanism import *
from .chemical_reaction_network import Species, Reaction, ComplexSpecies, Multimer

class Reversible_Bimolecular_Binding(Mechanism):
    def __init__(self, name="reversible_bimolecular_binding",
                 mechanism_type="bimolecular_binding"):
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    def update_species(self, s1, s2, **keywords):
        complex = ComplexSpecies([s1, s2])
        return [complex]

    def update_reactions(self, s1, s2, component = None, kb = None, ku = None, \
                                              part_id = None,complex=None, **keywords):

        #Get Parameters
        if part_id == None:
            repr(s1)+"-"+repr(s2)
        if kb == None and component != None:
            kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
        if ku == None and component != None:
            ku = component.get_parameter("ku", part_id = part_id, mechanism = self)
        if component == None and (kb == None or ku == None):
            raise ValueError("Must pass in a Component or values for kb, ku.")
        if(complex==None):
            complex = ComplexSpecies([s1, s2])
        rxns = [Reaction([s1, s2], [complex], k=kb, k_rev=ku)]
        return rxns


class One_Step_Cooperative_Binding(Mechanism):
    """A reaction where n binders (A) bind to 1 bindee (B) in one step
       n A + B <--> nA:B
    """
    def __init__(self, name="one_step_cooperative_binding",
                 mechanism_type="cooperative_binding"):
        Mechanism.__init__(self, name, mechanism_type)

    def update_species(self, binder, bindee, complex_species = None, cooperativity=None, component = None, part_id = None, **kwords):

        if part_id == None:
            part_id = repr(binder)+"-"+repr(bindee)

        if cooperativity == None and component != None:
            cooperativity = component.get_parameter("cooperativity", part_id = part_id, mechanism = self)
        elif component == None and cooperativity == None:
            raise ValueError("Must pass in a Component or values for cooperativity")

        complex = None
        if complex_species is None:
            complex_name = None
            material_type = None
        elif isinstance(complex_species, str):
            complex_name = complex_species
            material_type = None
        elif isinstance(complex_species, Species):
            complex = complex_species
            material_type = complex_species.material_type
        else:
            raise TypeError("complex_species keyword must be a str, Species, or None.")

        if complex == None:
            complex = ComplexSpecies([binder]*int(cooperativity)+[bindee], name = complex_name, material_type = material_type)

        
        return [complex]

    def update_reactions(self, binder, bindee, complex_species = None, component = None, kb = None, ku = None, part_id = None, cooperativity=None, **kwords):

        complex = self.update_species(binder, bindee, cooperativity = cooperativity, part_id = part_id, component = component, **kwords)[0]

        #Get Parameters
        if part_id == None:
            part_id = repr(binder)+"-"+repr(bindee)
        if kb == None and component != None:
            kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
        if ku == None and component != None:
            ku = component.get_parameter("ku", part_id = part_id, mechanism = self)
        if cooperativity == None and component != None:
            cooperativity = component.get_parameter("cooperativity", part_id = part_id, mechanism = self)
        if component == None and (kb == None or ku == None or cooperativity == None):
            raise ValueError("Must pass in a Component or values for kb, ku, and coopertivity.")


        rxns = []
        rxns += [
            Reaction(inputs=[binder, bindee], outputs=[complex],
                     input_coefs=[cooperativity, 1], output_coefs=[1], k=kb,
                     k_rev=ku)]
        return rxns


class Two_Step_Cooperative_Binding(Mechanism):
    """A reaction where n binders (s1) bind to 1 bindee (s2) in two steps
       n A <--> nx_A
       nx_A <--> nx_A:B
    """
    def __init__(self, name="two_step_cooperative_binding",
                 mechanism_type="cooperative_binding"):
        Mechanism.__init__(self, name, mechanism_type)

    def update_species(self, binder, bindee, component = None, complex_species = None, n_mer_species = None, cooperativity=None, part_id = None, **keywords):

        if part_id == None:
            part_id = repr(binder)+"-"+repr(bindee)

        if cooperativity == None and component != None:
            cooperativity = component.get_parameter("cooperativity", part_id = part_id, mechanism = self)
        elif component == None and cooperativity == None:
            raise ValueError("Must pass in a Component or values for cooperativity")

        n_mer = None
        if n_mer_species is None:
            n_mer_name = binder.name
            n_mer_material = binder.material_type
        elif isinstance(n_mer_species, str):
            n_mer_name = n_mer_species
            n_mer_material = "complex"
        elif isinstance(n_mer_species, Species):
            n_mer = n_mer_species
        else:
            raise TypeError("n_mer_species keyword nust be a str, Species, or None. Not "+str(n_mer_species))

        if n_mer is None:
            n_mer = Multimer(binder, cooperativity, name = n_mer_name, material_type = n_mer_material)

        complex = None
        if complex_species is None:
            complex_name = None
            material_type = "complex"
        elif isinstance(complex_species, str):
            complex_name = complex_species
            material_type = "complex"
        elif isinstance(complex_species, Species):
            complex = complex_species
        else:
            raise TypeError("complex_species keyword must be a str, Species, or None. Not "+str(complex_species))

        if complex == None:
            complex = ComplexSpecies([n_mer, bindee], name = complex_name)
        return [complex, n_mer]

    def update_reactions(self, binder, bindee, kb = None, ku = None, component = None, part_id = None, cooperativity=None, complex_species = None, n_mer_species = None, **keywords):
        """
        Returns reactions:
        cooperativity binder <--> n_mer, kf = kb1, kr = ku1
        n_mer + bindee <--> complex, kf = kb2, kr = ku2
        :param s1:
        :param s2:
        :param kb:
        :param ku:
        :param cooperativity:
        :param keywords:
        :return:
        """

        if part_id == None:
            repr(binder)+"-"+repr(bindee)
        if (kb == None or ku == None or cooperativity == None) and Component != None:
            kb1 = component.get_parameter("kb1", part_id = part_id, mechanism = self)
            kb2 = component.get_parameter("kb2", part_id = part_id, mechanism = self)
            ku1 = component.get_parameter("ku1", part_id = part_id, mechanism = self)
            ku2 = component.get_parameter("ku2", part_id = part_id, mechanism = self)
            cooperativity = component.get_parameter("cooperativity", part_id = part_id, mechanism = self)
        elif component == None and (kb == None or ku == None or cooperativity == None):
            raise ValueError("Must pass in a Component or values for kb, ku, and cooperativity")
        elif len(kb) != len(ku) != 2:
            raise ValueError("kb and ku must contain 2 values each for "
                             "two-step binding")
        else:
            kb1, kb2 = kb
            ku1, ku2 = ku
        n_mer_name = f"{cooperativity}x_{binder.material_type}_{binder.name}"
        n_mer = ComplexSpecies([binder], name = n_mer_name)
        if(complex == None):
            complex = ComplexSpecies([n_mer, bindee])

        complex, n_mer = self.update_species(binder, bindee, component = None, complex_species = None, n_mer_species = None, cooperativity=None, part_id = None, **keywords)

        rxns = [
            Reaction(inputs=[binder], outputs=[n_mer],
                     input_coefs=[cooperativity], output_coefs=[1], k=kb1,
                     k_rev=ku1),
            Reaction(inputs=[n_mer, bindee], outputs=[complex], k=kb2,
                     k_rev=ku2)]

        return rxns


class One_Step_Binding(Mechanism):
    def __init__(self, name="one_step_binding",
                 mechanism_type="binding"):
        Mechanism.__init__(self, name, mechanism_type)

    def update_species(self, species, component = None, complex_species = None, part_id = None, **keywords):
        if part_id == None:
            part_id = ""
            for s in self.internal_species:
                part_id += s.name+"_"
            part_id = part_id[:-1]

        if complex_species is None:
            complex_species = ComplexSpecies(species)

        return species + [complex_species]


    def update_reactions(self, species, component = None, complex_species = None, part_id = None, kb = None, ku = None, **keywords):
        if part_id is None:
            part_id = ""
            for s in self.internal_species:
                part_id += s.name+"_"
            part_id = part_id[:-1]

        if (kb == None or ku == None) and Component != None:
            kb = component.get_parameter("kb", part_id = part_id, mechanism = self)
            ku = component.get_parameter("ku", part_id = part_id, mechanism = self)
        elif component is None and (kb == None or ku == None):
            raise ValueError("Must pass in a Component or values for kb and ku")

        if complex_species is None:
            complex_species = ComplexSpecies(species)

        return [Reaction(inputs = species, outputs = [complex_species], k = kb, k_rev = ku)]